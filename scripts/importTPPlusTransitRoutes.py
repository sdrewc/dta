__copyright__   = "Copyright 2011 SFCTA"
__license__     = """
    This file is part of DTA.

    DTA is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    DTA is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with DTA.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging
import sys

import dta
from dta.TPPlusTransitRoute import TPPlusTransitRoute
from dta.DynameqTransitLine import TransitLine
from dta.Algorithms import pairwise, ShortestPaths
#from dta.Network import Network

#from pbCore.utils.itertools2 import pairwise
#from pbCore.dynameq.transitLine import TransitLine
#from pbModels.algorithms.shortestPaths import ShortestPaths
#from pbCore.dynameq.error import TPPlus2DynameqError

def convertHeadway2HHMM(headwayInMin):

    hours = headwayInMin / 60
    minutes = headwayInMin - hours * 60

    if hours < 10:
        hours = '0%d' % hours
    else:
        hours = '%d' % hours
    if minutes < 10:
        minutes = '0%d' % minutes
    else:
        minutes = '%d' % minutes

    return "%s%s" % (hours, minutes)

def convertStartTime2HHMMSS(startTimeInMin):

    hours = startTimeInMin / 60
    minutes = startTimeInMin - hours * 60

    if hours < 10:
        hours = '0%d' % hours
    else:
        hours = '%d' % hours
    if minutes < 10:
        minutes = '0%d' % minutes
    else:
        minutes = '%d' % minutes

    return "%s:%s:00" % (hours, minutes)



class TPPlus2Dynameq(object):
    """Converts TPPlus Network elemements to the equivalent Dynameq ones"""
    
    @classmethod
    def convertRoute(cls, dynameqNet, tpplusRoute, doShortestPath=True):
        """Convert the input tpplusRoute to an equivalent Dynameq route"""
        DWELL_TIME = 30

        tRoute = tpplusRoute

        for edge in dynameqNet.iterLinks():
            edge.cost = edge.euclideanLength()
            if edge.isConnector():
                edge.cost = sys.maxint

        
        dNodeSequence = []
        for tNode in tRoute.iterTransitNodes():
            if not dynameqNet.hasNodeForId(tNode.nodeId):
                continue
            dNode = dynameqNet.getNodeForId(tNode.nodeId)
            dNodeSequence.append(dNode)

        if len(dNodeSequence) == 0:
            errorMessage = ('Tpplus route %s cannot be converted to Dynameq because '
                            'none of its nodes is in the Dynameq network' % tRoute.name)
            logging.error(errorMessage)
            raise TPPlus2DynameqError(errorMessage)
                                              
        if len(dNodeSequence) == 1:
            errorMessage = ('Tpplus route %s cannot be converted to Dyanmeq because only '
                                      'one of its nodes is in the Dynameq network' % tRoute.name)
            logging.error(errorMessage)            
            raise TPPlus2DynameqError(errorMessage)

        dRoute = dta.DynameqTransitLine.TransitLine(dynameqNet, tRoute.name, 'label1', '0', 'Generic', '15:30:00', '00:20:00', 10)
        for dNodeA, dNodeB in dta.Algorithms.pairwise(dNodeSequence):
            
            if dynameqNet.hasLinkForNodeIdPair(dNodeA.getId(), dNodeB.getId()):
                dLink = dynameqNet.getLinkForNodeIdPair(dNodeA.getId(), dNodeB.getId())
                dSegment = dRoute.addSegment(dLink, 0)
                #print 'added link', dLink.iid

                tNodeB = tRoute.getTransitNode(dLink.nodeBid)
                if tNodeB.isStop:
                    dSegment.dwell = DWELL_TIME
                
            else:
                if doShortestPath:
                    print 'I am running the SP. Root node', dNodeA.getId()
                    ShortestPaths.labelCorrectingWithLabelsOnNodes(dynameqNet, dNodeA)
                    if dNodeB.label == sys.maxint:
                        continue

                    pathNodes = ShortestPaths.getShortestPath(dNodeA, dNodeB)

                    for pathNodeA, pathNodeB in pairwise(pathNodes):
                        dLink = dynameqNet.getLink(pathNodeA.id, pathNodeB.id)
                        dSegment = dRoute.addSegment(dLink, 0)

                    tNodeB = tRoute.getTransitNode(dLink.nodeBid)
                    if tNodeB.isStop:
                        dSegment.dwell = DWELL_TIME
                else:
                    pass
                        
        
        dRoute.isPathValid()
        return dRoute

if __name__ == "__main__":

    INPUT_DYNAMEQ_NET_DIR         = sys.argv[1]
    INPUT_DYNAMEQ_NET_PREFIX      = sys.argv[2]
    TRANSIT_LINES                 = sys.argv[3]

    dta.VehicleType.LENGTH_UNITS= "feet"
    dta.Node.COORDINATE_UNITS   = "feet"
    dta.RoadLink.LENGTH_UNITS   = "miles"

    dta.setupLogging("dtaInfo.log", "dtaDebug.log", logToConsole=True)
    
    scenario = dta.DynameqScenario(dta.Time(0,0), dta.Time(23,0))
    scenario.read(INPUT_DYNAMEQ_NET_DIR, INPUT_DYNAMEQ_NET_PREFIX) 
    net = dta.DynameqNetwork(scenario)
    net.read(INPUT_DYNAMEQ_NET_DIR, INPUT_DYNAMEQ_NET_PREFIX)

    for tpplusRoute in dta.TPPlusTransitRoute.read(net, TRANSIT_LINES):

        dynameqRoute = TPPlus2Dynameq.convertRoute(net, tpplusRoute)

        

    


    

    
    

    
                
