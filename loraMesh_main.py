#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 LoRaMeshSim 0.1.0: simulate collisions and duty cycle in LoRa mesh
 Copyright © 2024 Yu Chen <yu.chen.2@glasgow.ac.uk>, Guo Shi <guo.shi@strath.ac.uk>,
                Yusuf Sambo <yusuf.sambo@glasgow.ac.uk>, Oluwakayode Onireti <oluwakayode.onireti@glasgow.ac.uk>,
                and Muhammad Imran <muhammad.imran@glasgow.ac.uk>

 This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
 International License. To view a copy of this license,
 visit https://creativecommons.org/licenses/by-nc-sa/4.0/.

 For commercial use, please contact us at yu.chen.2@glasgow.ac.uk

 $Date: 2024-01-24 11:33:42 +0000 (Wen, 24 January 2024) $
 $Revision: 243 $
"""

import simpy
import random
import numpy as np
import math
import pandas as pd
import matplotlib.pyplot as plt
from class_myNode import Node, GW
from functions import calculateRSSI, collectData
from matplotlib.lines import Line2D

#
# "main" program
#
if __name__ == '__main__':
    graphics = 1                            # graphics = 1 to plot the figure of node locations and coverages

    # parameters
    sf = 12                                 # valid values: {7, 8, 9, 10, 11, 12}
    cr = 1                                  # valid values: {1, 2, 3, 4}
    bw = 125                                # valid values: {125, 250, 500}
    dens = 2                                # deployment density factor (>=1)
    avgSendTime = 15*60*1000                # in millisecond
    simtime = 1*60*60*1000                  # in millisecond
    nrNodes = 20                            # the number of sensor nodes, excluding the gateway
    dataPacketLen = 40                      # the length of one data packet in byte
    ACKPacketLen = 5                        # the length of one acknowledgement packet in byte
    routingPacketLen = 5                    # the length of one routing request packet in byte
    routingRequestPacketLen = 5             # the length of one routing discovery packet in byte

    # A dictionary containing nodes
    nodes = {}

    # A complex dictionary to describe packets are the surroundings of node i.
    # Will be used to judge if there is signal collision.
    # Data structure will be {0: [...], ...,i: [{'packet': node.packet, 'status': 0/1}, ..., {}], ..., nrNodes: [...], 'gw': [...]},
    # denoting the node.packet is at the surrounding of node i. 'status' 1 means the packet targets nodes i, 0 otherwise.
    packetsAt = {}
    for i in range(0, nrNodes):
        packetsAt[i] = []
    packetsAt['gw'] = []
    env = simpy.Environment()

    # The working status of each node.
    # "working" is occupied when the node is transmitting, receiving, or waiting for ACK.
    # During "working" is occupied, the node cannot transmit new message.
    # During "working" is occupied and node.waiting = 0, the node cannot receive new message.
    working = {}
    for i in range(0, nrNodes):
        working[i] = simpy.PreemptiveResource(env, capacity=1)   # capacity reflects the number of frequency carriers.
    working['gw'] = simpy.PreemptiveResource(env, capacity=1)

    # radio settings
    freq = random.choice([860000000, 864000000, 868000000])
    Ptx = 14
    gamma = 2.08
    d0 = 40.0
    var = 0
    Lpld0 = 127.41
    GL = 0

    # sensitivity table. According to Table 1 in Bor, Martin C., et al. "Do LoRa low-power wide-area networks scale?."
    # Proceedings of the 19th ACM International Conference on Modeling, Analysis and Simulation of Wireless and Mobile
    # Systems. 2016.
    sf7 = np.array([-126.5, -124.25, -120.75])
    sf8 = np.array([-127.25, -126.75, -124.0])
    sf9 = np.array([-131.25, -128.25, -127.5])
    sf10 = np.array([-132.75, -130.25, -128.75])
    sf11 = np.array([-134.5, -132.75, -128.75])
    sf12 = np.array([-133.25, -132.25, -132.25])
    sensi = np.array([sf7, sf8, sf9, sf10, sf11, sf12])
    if bw == 125:
        bw_index = 0
    elif bw == 250:
        bw_index = 1
    elif bw == 500:
        bw_index = 2
    minsensi = sensi[sf - 7, bw_index]
    Lpl = Ptx - minsensi
    print("sensitivity", minsensi)
    maxDist = d0*(math.e**((Lpl-Lpld0)/(10.0*gamma)))
    print("maxDist:", maxDist)

    # gateway placement
    gwx = 0
    gwy = 0
    xmax = gwx + maxDist * nrNodes + 20
    ymax = gwy + maxDist * nrNodes + 20

    # prepare graphics
    if (graphics == 1):
        plt.figure()
        plt.xlim([gwx - 20, xmax + 20])
        plt.ylim([-xmax/2 - 20, xmax/2 + 20])
        plt.ion()
        ax = plt.gcf().gca()
        # plot gateway
        ax.add_artist(plt.Circle((gwx, gwy), 3, fill=True, color='red'))
        ax.add_artist(plt.Circle((gwx, gwy), maxDist, fill=False, color='red'))

    for i in range(0, nrNodes):
        # generate sensor nodes
        node = Node(i, avgSendTime, dataPacketLen, ACKPacketLen, routingRequestPacketLen, routingPacketLen, gwx, gwy, maxDist, dens, nodes, sf, cr, bw, Ptx, freq)
        nodes[i] = node
        # plot sensor nodes
        if (graphics == 1):
            ax.add_artist(plt.Circle((node.x, node.y), 2, fill=True, color='green'))
            ax.add_artist(plt.Circle((node.x, node.y), maxDist, fill=False, color='green'))

    # generate gateway
    nodes['gw'] = GW(ACKPacketLen, routingPacketLen, gwx, gwy, maxDist, nrNodes, sf, cr, bw, Ptx, freq)

    # calculate RSSI between nodes.
    calculateRSSI(nodes, Lpld0, gamma, d0, GL, gwx, gwy)

    # prepare show
    if (graphics == 1):
        plt.xlim([gwx - maxDist + 20, nodes[nrNodes-1].x + maxDist + 20])
        plt.ylim([-(nodes[nrNodes-1].x - gwx)/2, (nodes[nrNodes-1].x - gwx)/2])
        legend1 = Line2D([], [], color="white", marker='o', markersize=4, markerfacecolor="red")
        legend2 = Line2D([], [], linewidth=0, color="red", marker='o', markersize=10, markerfacecolor="white")
        legend3 = Line2D([], [], color="white", marker='o', markersize=4, markerfacecolor="green")
        legend4 = Line2D([], [], linewidth=0, color="green", marker='o', markersize=10, markerfacecolor="white")
        plt.legend((legend1, legend2, legend3, legend4), ('Gateway', 'Gateway coverage', 'Sensor node', 'Sensor node coverage'), numpoints=1, loc=1)
        plt.xlabel('Horizontal Position (meters)')
        plt.ylabel('Vertical Position (meters)')
        plt.title('Node Locations and Coverages')
        plt.draw()
        plt.show()

    # 1 skip routing and use Andrei Broder Algorithm to generate a random spanning tree as the topology
    # 1.1 obtain the neighbors of each node.
    neighbor = []
    for i in range(nrNodes + 1):
        neighborMax = i + dens
        neighborMin = i - dens
        if neighborMax > nrNodes:
            neighborMax = nrNodes
        if neighborMin < 0:
            neighborMin = 0
        neighbor.append(([j for j in range(neighborMin, i)] + [j for j in range(i + 1, neighborMax + 1)]))

    # generate random spanning tree
    adjMatrix_spanTree = np.zeros((nrNodes + 1, nrNodes + 1))
    traversedNode = []
    leftNode = [i for i in range(nrNodes + 1)]
    startNode = random.choice(leftNode)
    traversedNode.append(startNode)
    leftNode.remove(startNode)
    while len(leftNode) > 0:
        while True:
            fromNode = random.choice(traversedNode)
            a = set(neighbor[fromNode])
            b = set(traversedNode)
            if not a.issubset(b):
                break
        while True:
            toNode = random.choice(neighbor[fromNode])
            if toNode not in traversedNode:
                break
        traversedNode.append(toNode)
        leftNode.remove(toNode)
        adjMatrix_spanTree[fromNode][toNode] = 1
        adjMatrix_spanTree[toNode][fromNode] = 1

    # obtain routing table
    ParentNode = []
    ChildNode = [0]
    findChildNode = False
    while len(ChildNode) > 0:
        GrandNode = ParentNode
        ParentNode = ChildNode
        ChildNode = []
        for parentNode in ParentNode:
            for cols in range(nrNodes + 1):
                if cols not in GrandNode:
                    if adjMatrix_spanTree[parentNode][cols] == 1:
                        if parentNode == 0:
                            nodes[cols - 1].nextHop = 'gw'
                        else:
                            nodes[cols - 1].nextHop = parentNode - 1
                        ChildNode.append(cols)

    # start simulation
    for i in range(0, nrNodes):
        env.process(collectData(env, nodes, working, packetsAt, nodes[i]))
    env.run(until=simtime)

    # results
    ToA = []
    nextHop = []
    DC = []                     # duty cycle
    index = []
    dataCollided = []
    dataLost = []
    ACKCollided = []
    ACKLost = []
    notReceiveACK = []
    generated = []
    nodes['gw'].received.append(None)
    received = nodes['gw'].received
    for i in nodes:
        ToA.append(nodes[i].accumToA)
        DC.append(nodes[i].accumToA/simtime)
        nextHop.append(nodes[i].nextHop)
        dataCollided.append(nodes[i].dataCollided)
        dataLost.append(nodes[i].dataLost)
        ACKCollided.append(nodes[i].ACKCollided)
        ACKLost.append(nodes[i].ACKLost)
        notReceiveACK.append(nodes[i].notReceiveACK)
        generated.append(nodes[i].generated)
        index.append('node'+str(i))

    result = pd.DataFrame(data={'nextHop': nextHop, 'ToA': ToA, 'DC': DC, 'dataCollided': dataCollided, 'dataLost': dataLost, \
                                'ACKCollided': ACKCollided, 'ACKLost': ACKLost, 'notReceiveACK': notReceiveACK, 'generated': generated, 'receivedFrom': received},
                          index=index)
    pd.set_option('display.max_columns', 20)
    #print(result[['nextHop', 'ToA', 'DC', 'dataCollided', 'dataLost', 'ACKCollided', 'ACKLost', 'generated', 'receivedFrom']])
    print(result[['nextHop', 'DC', 'dataCollided', 'dataLost', 'ACKCollided', 'ACKLost', 'notReceiveACK', 'generated', 'receivedFrom']])
    result.to_csv('result.csv')
    print('generated:', result['generated'].sum())
    print('dataCollided:', result['dataCollided'].sum())
    print('dataLost:', result['dataLost'].sum())
    print('received:', result['receivedFrom'].sum())
    print('ACKCollided:', result['ACKCollided'].sum())
    print('ACKLost:', result['ACKLost'].sum())                 # = ACKCollided.sum() as the node would not transmit when waiting for ACK
    print('notReceiveACK:', result['notReceiveACK'].sum())     # = dataLost.sum() + ACKLost.sum()
    print('delivery rate:', result['receivedFrom'].sum() / result['generated'].sum())






