import math
import numpy as np
import random
import simpy

#
# this function computes the time on air of a packet
#
def timeOnAir(sf, cr, plen, bw):
    H = 0        # implicit header disabled (H=0) or not (H=1)
    DE = 0       # low data rate optimization enabled (=1) or not (=0)
    Npream = 8   # number of preamble symbol (12.25  from Utz paper)

    if bw == 125 and sf in [11, 12]:
        # low data rate optimization mandated for BW125 with SF11 and SF12
        DE = 1
    if sf == 6:
        # can only have implicit header with SF6
        H = 1

    Tsym = (2.0**sf)/bw
    Tpream = (Npream + 4.25)*Tsym
    payloadSymbNB = 8 + max(math.ceil((8.0*plen-4.0*sf+28+16-20*H)/(4.0*(sf-2*DE)))*(cr+4),0)
    Tpayload = payloadSymbNB * Tsym
    return Tpream + Tpayload

#
# calculate RSSI when the distance between two nodes is less than comDist.
#
def calculateRSSI(nodes, Lpld0, gamma, d0, GL, gwx, gwy):
    for i in nodes:
        for j in nodes:
            if j != i:
                dist = np.sqrt((nodes[i].x - nodes[j].x)**2 + (nodes[i].y - nodes[j].y)**2)   # distance between two nodes
                if dist <= nodes[i].ACK.comDist:
                    lpl = Lpld0 + 10 * gamma * math.log(dist / d0)
                    nodes[i].ACK.RSSI[j] = nodes[i].ACK.Ptx - GL - lpl
                if dist <= nodes[i].routing.comDist:
                    lpl = Lpld0 + 10 * gamma * math.log(dist / d0)
                    nodes[i].routing.RSSI[j] = nodes[i].routing.Ptx - GL - lpl
                if i != 'gw':                                               # gw doesnt have dataPacket and routingRequest
                    if dist <= nodes[i].dataPacket.comDist:
                        lpl = Lpld0 + 10 * gamma * math.log(dist / d0)
                        nodes[i].dataPacket.RSSI[j] = nodes[i].dataPacket.Ptx - GL - lpl
                    if dist <= nodes[i].routingRequest.comDist:
                        lpl = Lpld0 + 10 * gamma * math.log(dist / d0)
                        nodes[i].routingRequest.RSSI[j] = nodes[i].routingRequest.Ptx - GL - lpl

#
# the process of collecting data and transmitting it
#
def collectData(env, nodes, working, packetsAt, node):
    msgID = 0
    while True:                                 # collect data continuously with exponential distribution
        msgID += 1
        yield env.timeout(random.expovariate(1.0/float(node.period)))
        #yield env.timeout(node.period)
        print(env.now, 'node', node.nodeID, 'collectData', '( working[', node.nodeID, '].count is', working[node.nodeID].count, ')')
        with working[node.nodeID].request(priority=0) as req:          # wait until node is free
            yield req
            try:
                node.generated += 1
                yield env.process(transmitData(env, nodes, packetsAt, working, node, node.nextHop, node.nodeID, msgID))  # wait until finishing transmit
            except simpy.Interrupt as interrupt:
                by = interrupt.cause.by
                print('node', node.nodeID, 'waiting for ACK from node', node.nextHop, 'got preempted by', by)

#
# function to transmit data packets and waits for ACK.
#
def transmitData(env, nodes, packetsAt, working, fromNode, toID, sourceID, msgID):
    if toID == None:
        print(env.now, 'no nextHop')                                    # !!! modified to wait until receiving routing
    else:
        print(env.now, 'node', fromNode.nodeID, 'start transmitting Data originally from node', sourceID, 'to node',
              toID, '(msgID is', msgID, ';working[', fromNode.nodeID, '].count is', working[fromNode.nodeID].count, ')')
        for i in fromNode.dataPacket.RSSI:
            if i != toID:
                if checkCollision(env, fromNode.dataPacket, packetsAt, i) == 1:  # the collided packet is labeled within checkCollision
                    pass                                                         # Due to collision, node i doesn't process it.
                else:                                                            # we can derive no receiving from no collision
                    if working[i].count < working[i].capacity or nodes[i].waiting == 1:  # if it's free or waiting for ACK
                        env.process(receiving(env, nodes, packetsAt, working, fromNode, fromNode.dataPacket, i, toID, sourceID, msgID))    # node i receives the packet even though \
                                                                                            # it will be discarded as node i is not the nextHop
                packetsAt[i].append({'packet': fromNode.dataPacket, 'status': 0})           # packets arrive at the surroundings of node i regardless of collision
                                                                                            # status 0 means the packet doesnt target node i.
            else:
                if checkCollision(env, fromNode.dataPacket, packetsAt, i) == 1:
                    fromNode.dataPacket.collided = 1
                    print(env.now, 'dataPacket from node', fromNode.nodeID, 'to node', i, 'is collided')
                else:
                    fromNode.dataPacket.collided = 0                        # possibly be changed after ToA
                    print(env.now, 'nextHop: working[', i, '].count is', working[i].count, 'nodes[', i, '].waiting is', nodes[i].waiting)
                    if working[i].count < working[i].capacity or nodes[i].waiting == 1:  # if it's free or waiting for ACK
                        env.process(receiving(env, nodes, packetsAt, working, fromNode, fromNode.dataPacket, i, toID, sourceID, msgID))    # nextHop starts receiving the packet
                        fromNode.dataPacket.received = 1
                    else:
                        fromNode.dataPacket.received = 0
                        print(env.now, 'node', i, 'cannot receive dataPacket from node', fromNode.nodeID, 'ogriginally from node', sourceID, 'as it`s transmitting')
                packetsAt[i].append({'packet': fromNode.dataPacket, 'status': 1})            # status 1 means the packet targets node i.

        yield env.timeout(fromNode.dataPacket.ToA)
        fromNode.accumToA += fromNode.dataPacket.ToA

        # finish transmitting
        for i in fromNode.dataPacket.RSSI:
            if i != toID:
                packetsAt[i].remove({'packet': fromNode.dataPacket, 'status': 0})
            else:
                packetsAt[i].remove({'packet': fromNode.dataPacket, 'status': 1})
        print(env.now, 'node', fromNode.nodeID, 'finish transmitting Data originally from node', sourceID,  'to node',
              toID, '(msgID is', msgID, ';working[', fromNode.nodeID, '].count is', working[fromNode.nodeID].count, ')')

        # count
        if fromNode.dataPacket.collided == 1:
            nodes[toID].dataCollided += 1
            print(env.now, 'node', toID, '.dataCollided +1')
            nodes[toID].dataLost += 1
            print(env.now, 'node', toID, '.dataLost +1', '; dataPacket from', sourceID, '(mesID:', msgID, ') is lost')
        else:
            if fromNode.dataPacket.received == 0:
                nodes[toID].dataLost += 1
                print(env.now, 'node', toID, '.dataLost +1', '; dataPacket from', sourceID, '(mesID:', msgID, ') is lost')

        # waiting for ACK
        fromNode.ACKTimer = env.process(fromNode.ACKTimerCreator(env, waitingTime=nodes[toID].ACK.ToA, ACKToA=nodes[toID].ACK.ToA))      # set a timer for ACK
        fromNode.waiting = 1
        print(env.now, 'node', fromNode.nodeID, 'start waiting for ACK from node', toID, fromNode.waiting)
        yield env.timeout(nodes[toID].ACK.ToA)              # the waiting time is not necessarily ToA
        fromNode.waiting = 0
        print(env.now, 'node', fromNode.nodeID, 'stop waiting for ACK from node', toID, fromNode.waiting)


#
# when a node receives a packet, its 'working' should be labeled as busy to prevent from sending at the same time.
#
def receiving(env, nodes, packetsAt, working, fromNode, packet, receivedID, toID, sourceID, msgID):
    relay = False
    with working[receivedID].request(priority=-1) as reqR:               # -1 will kick out 'waiting for ACK' from 'working' if it is waiting
        yield reqR
        print(env.now, 'node', receivedID, 'start receiving', packet.type, 'from node', fromNode.nodeID, '(working[', receivedID, '].count is', working[receivedID].count, ')')
        yield env.timeout(packet.ToA)
        print(env.now, 'node', receivedID, 'stop receiving', packet.type, 'from node', fromNode.nodeID, '(working[', receivedID, '].count is', working[receivedID].count, ')')

        # If transmission is successful
        if packet.collided == 0 and packet.received == 1:                   # completely received
            print(env.now, packet.type, 'from node', fromNode.nodeID, 'has been transmitted to', receivedID, 'successfully')
            if receivedID != toID:                                          # discard if the packet is not for me
                print(env.now, packet.type, 'from node', fromNode.nodeID, 'is discarded by', receivedID)
            else:                                                           # process only if the packet is for me

                # If the packet is ACK
                if packet.type == 'ACK':
                    print(env.now, 'node', receivedID, 'receives ACK from', fromNode.nodeID)
                    try:
                        nodes[receivedID].ACKTimer.interrupt()               # interrupt the ACKTimer
                    except:                                                  # If the node has stopped waiting for ACK
                        print(env.now, 'node', receivedID, 'has stopped waiting for the ACK, so the ACK is discarded')

                # send ACK back and queue a relay if the packet is dataPacket
                elif packet.type == 'dataPacket':                             # Transmit ACK back if it is a dataPacket
                    # count if the dataPacket arrives at gateway
                    if receivedID == 'gw':
                        nodes['gw'].received[sourceID] += 1
                    # ACK
                    print(env.now, 'node', receivedID, 'start transmitting ACK back to node', fromNode.nodeID)
                    for i in nodes[receivedID].ACK.RSSI:
                        if i != fromNode.nodeID:
                            if checkCollision(env, nodes[receivedID].ACK, packetsAt, i) == 1:  # the collided packet is labeled within checkCollision
                                pass  # Due to collision, node i doesn't process it.
                            else:  # we can derive no receiving from no collision
                                if working[i].count < working[i].capacity or nodes[i].waiting == 1:  # if it's free or waiting for ACK
                                    env.process(receiving(env, nodes, packetsAt, working, nodes[receivedID], nodes[receivedID].ACK, i, fromNode.nodeID, sourceID, msgID))  # node i receives the packet even though \
                                                                                                                                                          # it will be discarded as node i is not the nextHop
                            packetsAt[i].append({'packet': nodes[receivedID].ACK, 'status': 0})  # packets arrive at the surroundings of node i regardless of collision
                                                                                               # status 0 means the packet doesnt target node i.
                        else:
                            if checkCollision(env, nodes[receivedID].ACK, packetsAt, i) == 1:
                                nodes[receivedID].ACK.collided = 1
                                print(env.now, 'ACK from node', receivedID, 'to node', i, 'is collided')
                            else:
                                nodes[receivedID].ACK.collided = 0  # possibly be changed after ToA
                                if working[i].count < working[i].capacity or nodes[i].waiting == 1:  # if it's free or waiting for ACK
                                    env.process(receiving(env, nodes, packetsAt, working, nodes[receivedID], nodes[receivedID].ACK, i, fromNode.nodeID, sourceID, msgID))  # starts receiving the packet
                                    nodes[receivedID].ACK.received = 1
                                else:
                                    nodes[receivedID].ACK.received = 0
                                    print(env.now, 'node', i, 'cannot receive ACK from node', receivedID, 'as it`s transmitting')
                            packetsAt[i].append({'packet': nodes[receivedID].ACK, 'status': 1})     # status 1 means the packet targets node i.
                    yield env.timeout(nodes[receivedID].ACK.ToA)
                    nodes[receivedID].accumToA += nodes[receivedID].ACK.ToA

                    # finish transmitting ACK
                    for i in nodes[receivedID].ACK.RSSI:
                        if i != fromNode.nodeID:
                            packetsAt[i].remove({'packet': nodes[receivedID].ACK, 'status': 0})
                        else:
                            packetsAt[i].remove({'packet': nodes[receivedID].ACK, 'status': 1})
                    print(env.now, 'node', receivedID, 'finish transmitting ACK', 'to node', fromNode.nodeID)

                    # count
                    if nodes[receivedID].ACK.collided == 1:
                        fromNode.ACKCollided += 1
                        print(env.now, 'node', fromNode.nodeID, '.ACKCollided +1')
                        fromNode.ACKLost += 1
                        print(env.now, 'node', fromNode.nodeID, '.ACKLost +1')
                    else:
                        if nodes[receivedID].ACK.received == 0:
                            fromNode.ACKLost += 1
                            print(env.now, 'node', fromNode.nodeID, '.ACKLost +1')

                    # need relay
                    relay = True

    # queue a relay
    if relay and receivedID != 'gw':
        with working[receivedID].request(priority=0) as reqT:  # wait until node is free
            yield reqT
            try:
                yield env.process(transmitData(env, nodes, packetsAt, working, nodes[receivedID], nodes[receivedID].nextHop, sourceID, msgID))
            except simpy.Interrupt as interrupt:
                by = interrupt.cause.by
                print(env.now, 'node', receivedID, 'waiting for ACK from node', nodes[receivedID].nextHop, 'got preempted by', by)


#
# check for collisions at nodes with RSSI >= minRSSI
# Note: called before a packet (or rather node) is inserted into the list
#
def checkCollision(env, packet, packetsAt, i):
    col = 0                 # flag needed since there might be several collisions for packet
    if packetsAt[i]:
        for other in packetsAt[i]:
            if other['packet'].nodeID != packet.nodeID:                          # ??? necessary
                if frequencyCollision(packet, other['packet']) and sfCollision(packet, other['packet']):
                    if other['status'] == 1:                    # the packet other['packet'] target this node
                        other['packet'].collided = 1            # other also got lost, if it wasn't lost already
                        print(env.now, other['packet'].type, 'from node', other['packet'].nodeID, 'to node', i, \
                              'is collided with', packet.type, 'from node', packet.nodeID)
                    col = 1
        return col
    return 0


#
# frequencyCollision, conditions
#
#        |f1-f2| <= 120 kHz if f1 or f2 has bw 500
#        |f1-f2| <= 60 kHz if f1 or f2 has bw 250
#        |f1-f2| <= 30 kHz if f1 or f2 has bw 125
def frequencyCollision(p1,p2):
    if (abs(p1.freq-p2.freq)<=120 and (p1.bw==500 or p2.freq==500)):
        return True
    elif (abs(p1.freq-p2.freq)<=60 and (p1.bw==250 or p2.freq==250)):
        return True
    else:
        if (abs(p1.freq-p2.freq)<=30):
            return True
    return False


#
# SF collision
#
def sfCollision(p1, p2):
    if p1.sf == p2.sf:
        return True
    return False