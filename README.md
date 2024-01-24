# LoRaMeshSim
## 1. Introduction
* LoRaMeshSim is a discrete-event simulator based on [LoRaSim](https://mcbor.github.io/lorasim/) and [SimPy](https://simpy.readthedocs.io/en/latest/), designed for simulating collisions and routing in LoRa mesh networks. It facilitates the development of new routing algorithms and the analysis of network reliability, scalability, and coverage.
* The design team belongs to the [Communication, Sensing & Imaging (CSI) group](https://www.gla.ac.uk/research/az/csi/) of the University of Glasgow.
* Team member: Yu Chen, Guo Shi, Dr Yusuf Sambo, Dr Oluwakayode Onireti, and Prof. Muhammad Imran
* Date: January 2024
* Contact: Yu Chen (Email: yu.chen.2@glasgow.ac.uk)

## 2. Related Publications
[1] Y. Chen, G. Shi, M. Al-Quraan, Y. Sambo, O. Onireti, and M. Imran, "LoRa Mesh-5G Integrated Network for Trackside Smart Weather Monitoring," *IEEE Transactions on Vehicular Technology*, 2024. (Accepted)
<br><a name="[2]"></a>[2] Y. Chen, G. Shi, Y. Sambo, O. Onireti, and M. Imran, "On the Scalability and Coverage of LoRa Mesh for Monitoring Linear Infrastructure," 2024. (Under review)

## 3. Repository Structure
<pre>
|--LoRaMesh_main.py: The main file for setting parameters and running the simulation.
|
|                   |--Node(): This class creates a sensor node.
|--class_myNode.py--|
|                   |--GW(): This class creates a gateway.
|
|                    |--DataPacket(): This class creates a data packet.
|                    |
|                    |--ACK(): This class creates an acknowledgment packet.
|--class_packets.py--|
|                    |--RoutingRequest(): This class creates a routing request packet.
|                    |
|                    |--Routing(): This class creates a routing discovery packet.
|
|                |--timeOnAir: This function computes the time on air of a packet.
|                |
|                |--calculateRSSI: This function calculates RSSI between two nodes.
|                |
|                |--collectData: This function triggers data collection and transmission.
|                |
|                |--transmitData: This function simulates the process of packet transmission.
|--functions.py--|
|                |--receiving: This function simulates the process of packet reception.
|                |
|                |--checkCollision: This function checks if there is a signal collision.
|                |
|                |--frequenceyCollsion: Called by checkCollision.
|                |
|                |--sfCollsion: Called by checkCollision.
|
|--result.csv: Save the simulation outputs.
</pre>

## 4. Usage Tips
### (1) Node placement
The nodes in the simulator are placed in a line as shown in the figure below. You can modify their locations in class_myNode.py if you want to place them in a two-dimensional plane.
<br><p align="center"><img src="https://github.com/YuChenUoG/LoRaMeshSim/assets/87127772/d774fa7d-d37c-44ee-8cad-83cd20bbbd31" alt="drawing" width="500"/></p>
### (2) Coverage
The source of the sensitivity table in the simulator is Table 1 of [Do LoRa low-power wide-area networks scale?](https://dl.acm.org/doi/abs/10.1145/2988287.2989163), in which it was measured utilizing two nodes deployed in different floors of a building. Thus, the coverage is much smaller than outdoors. You can modify the sensitivity table in LoRaMesh_main.py if you want to simulate outdoor coverage.
### (3) Routing Algorithm
The current version (0.1.0) does not include a routing algorithm. The routing tables are determined by a random spanning tree generated using [Andrei Broder](https://www.cs.cmu.edu/afs/cs/academic/class/15859n-f18/RelatedWork/Broder-GenRanSpanningTrees.pdf) and [David Alduous](https://epubs.siam.org/doi/abs/10.1137/0403039?casa_token=vOUjS88woZsAAAAA:yEB9iQIBtjkXKWLYl03rkBsMRFeznrV2zfh514q2vgqsTglPW9t55awoQUegywLUZMF1c793EHezLw) algorithm. We have proposed a routing algorithm in [[2]](#[2]) and will upload its source code to the repository when the paper is accepted.

## 5. Changelog
### 0.1.0 - 2024-01-24
Initial release.



