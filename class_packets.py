from functions import timeOnAir

#
# This class creates a data packet (associated with a node)
#
class DataPacket():
    def __init__(self, nodeID, plen, sf, cr, bw, Ptx, freq, maxDist):
        self.nodeID = nodeID
        self.plen = plen
        self.sf = sf
        self.cr = cr
        self.bw = bw
        self.freq = freq
        self.Ptx = Ptx
        self.ToA = timeOnAir(self.sf, self.cr, self.plen, self.bw)
        self.type = 'dataPacket'

        # Here, comDist of all the nodes = maxDist.
        # If using different sf, Ptx, or bw, comDist should be calculated accordingly.
        self.comDist = maxDist

        # includes all the nodes that can receive this packet with RSSI >= minRSSI.
        # will calculate after all the nodes are generated
        self.RSSI = {}

        # denote if packet is collided  or received
        self.collided = 0
        self.received = 0

#
# This class creates an acknowledgement packet (associated with a node)
#
class ACK():
    def __init__(self, nodeID, plen, sf, cr, bw, Ptx, freq, maxDist):
        self.nodeID = nodeID
        self.plen = plen
        self.sf = sf
        self.cr = cr
        self.bw = bw
        self.freq = freq
        self.Ptx = Ptx
        self.ToA = timeOnAir(self.sf, self.cr, self.plen, self.bw)
        self.type = 'ACK'

        # Here, comDist of all the nodes = maxDist.
        # If using different sf, Ptx, or bw, comDist should be calculated accordingly.
        self.comDist = maxDist

        # includes all the nodes that can receive this packet with RSSI >= minRSSI.
        # will calculate after all the nodes are generated
        self.RSSI = {}

        # denote if packet is collided or received
        self.collided = 0
        self.received = 0

#
# This class creates a routing reqeust packet (associated with a node)
#
class RoutingRequest():
    def __init__(self, nodeID, plen, sf, cr, bw, Ptx, freq, maxDist):
        self.nodeID = nodeID
        self.plen = plen
        self.sf = sf
        self.cr = cr
        self.bw = bw
        self.freq = freq
        self.Ptx = Ptx
        self.ToA = timeOnAir(self.sf, self.cr, self.plen, self.bw)
        self.type = 'routingRequest'

        # Here, comDist of all the nodes = maxDist.
        # If using different sf, Ptx, or bw, comDist should be calculated accordingly.
        self.comDist = maxDist

        # includes all the nodes that can receive this packet with RSSI >= minRSSI.
        # will calculate after all the nodes are generated
        self.RSSI = {}

        # denote if packet is collided or received
        self.collided = 0
        self.received = 0

#
# This class creates a routing discovery packet (associated with a node)
#
class Routing():
    def __init__(self, nodeID, plen, sf, cr, bw, Ptx, freq, maxDist):
        self.nodeID = nodeID
        self.plen = plen                            # not fixed!!!!!
        self.sf = sf
        self.cr = cr
        self.bw = bw
        self.freq = freq
        self.Ptx = Ptx
        self.ToA = timeOnAir(self.sf, self.cr, self.plen, self.bw)      # called after self.plen change
        self.type = 'routing'

        # Here, comDist of all the nodes = maxDist.
        # If using different sf, Ptx, or bw, comDist should be calculated accordingly.
        self.comDist = maxDist

        # includes all the nodes that can receive this packet with RSSI >= minRSSI.
        # will calculate after all the nodes are generated
        self.RSSI = {}

        # denote if packet is collided or received
        self.collided = 0
        self.received = 0