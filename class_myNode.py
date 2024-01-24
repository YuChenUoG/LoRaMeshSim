import random
from class_packets import DataPacket, ACK, RoutingRequest, Routing
import simpy

#
# This class creates a sensor node
#
class Node():
    def __init__(self, nodeID, period, dataPacketLen, ACKPacketLen, routingRequestPacketLen, routingPacketLen,  \
                 gwx, gwy, maxDist, dens, nodes, sf, cr, bw, Ptx, freq):
        self.nodeID = nodeID
        self.period = period
        self.nextHop = None        # obtain from routing
        self.accumToA = 0          # accumulative ToA for calculating duty cycle
        self.generated = 0         # the number of dataPackets generated in the node
        self.dataCollided = 0      # the number of dataPackets collided in the node
        self.dataLost = 0          # the number of dataPackets lost in the node, including dataCollided
        self.ACKCollided = 0       # the number of ACKPackets collided in the node
        self.ACKLost = 0           # the number of ACKPackets lost in the node, including ACKCollided
        self.waiting = 0           # if the node is waiting for ACK
        self.ACKTimer = None       # After sending dataPacket, creat a timer to waiting for ACK
        self.notReceiveACK = 0     # The number of ACK that the node doesn't receive after sending dataPacket due to dataLost or ACKLost

        # place nodes
        self.y = gwy
        k = random.random()
        if nodeID == 0:
            self.x = gwx + maxDist/(dens + k)
        else:
            self.x = nodes[nodeID-1].x + maxDist/(dens + k)

        # packets
        self.dataPacket = DataPacket(nodeID, dataPacketLen, sf, cr, bw, Ptx, freq, maxDist)
        self.ACK = ACK(nodeID, ACKPacketLen, sf, cr, bw, Ptx, freq, maxDist)
        self.routingRequest = RoutingRequest(nodeID, routingRequestPacketLen, sf, cr, bw, Ptx, freq, maxDist)
        self.routing = Routing(nodeID, routingPacketLen, sf, cr, bw, Ptx, freq, maxDist)

    def ACKTimerCreator(self, env, waitingTime, ACKToA):
        print(env.now, 'node', self.nodeID, 'sets a ACKTimer')
        try:
            yield env.timeout(waitingTime + ACKToA)
            print(env.now, 'node', self.nodeID, 'stops the ACKTimer without receiving ACK')
            # does not receive the ACK
            self.notReceiveACK += 1
            print(env.now, 'node', self.nodeID, '.ACKLost_ +1')
            print(env.now, 'node', self.nodeID, 'deletes its routing table')          # !!! modify after adding routing
        except simpy.Interrupt:
            print(env.now, 'node', self.nodeID, '`s ACKTimer is interrupted as ACK received')

#
# This class creates a gateway
#
class GW():
    def __init__(self, ACKPacketLen, routingPacketLen, gwx, gwy, maxDist, nrNodes, sf, cr, bw, Ptx, freq):
        self.nodeID = 'gw'
        self.y = gwy
        self.x = gwx
        self.accumToA = 0          # accumulative ToA for calculating duty cycle
        self.dataCollided = 0      # the number of dataPackets collided in the node
        self.dataLost = 0          # the number of dataPackets lost in the node, including dataCollided
        self.ACKCollided = None    # gw dosen't receive ACK
        self.ACKLost = None        # gw dosen't receive ACK
        self.nextHop = None        # gw dosen't have nextHop
        self.generated = None      # gw dosent generate
        self.received = [0]*nrNodes
        self.waiting = 0           # if the node is waiting for ACK. GW waits for ACK only for DL message.
        self.notReceiveACK = 0     # The number of ACK that the node doesn't receive after sending dataPacket due to dataLost or ACKLost

        # packets
        self.ACK = ACK(self.nodeID, ACKPacketLen, sf, cr, bw, Ptx, freq, maxDist)
        self.routing = Routing(self.nodeID, routingPacketLen, sf, cr, bw, Ptx, freq, maxDist)

