import pandas as pd
import os
import json
import requests
import re

# Define the mapping
mapping = {
    "transmissionState:vector": 0xF8000006,
    "passedUpPk:vector(count)": 0xF8000006,
    "droppedPkWrongPort:vector(count)": 0xF8000006,
    "droppedPkBadChecksum:vector(count)": 0xF8000006,
    "servingCell:vector": 0xF8000006,
    "txPk:vector(packetBytes)": 0x03000000, # bits *8
    "rxPkOk:vector(packetBytes)": 0x03000000, # bits *8
    "passedUpPk:vector(packetBytes)": 0x03000000, # bits *8
    "receivedPacketFromLowerLayer:vector(packetBytes)": 0x03000000, # bits *8
    "posLongCar:vector": 0xC4B24924, # *pi/180
    "posLatCar:vector": 0xC4B24924, # *pi/180
    "posZCar:vector": 0xC4964924,
    "packetSent:vector(packetBytes)": 0x03000000, # bits *8
    "rcvdPkFromHl:vector(packetBytes)": 0x03000000, # bits *8
    "receivedPacketFromUpperLayer:vector(packetBytes)": 0x03000000, # bits *8
    "sentPacketToLowerLayer:vector(packetBytes)": 0x03000000, # bits *8
    "packetReceived:vector(packetBytes)": 0x03000000, # bits *8
    "harqErrorRate_1st_Ul:vector": 0xF8000001,
    "harqErrorRateUl:vector": 0xF8000001,
    "harqErrorRate_2nd_Ul:vector": 0xF8000001,
    "harqTxAttemptsUl:vector": 0xF8000006,
    "sentPacketToUpperLayer:vector(packetBytes)": 0x03000000, # bits *8
    "rlcPacketLossUl:vector": 0xF8000001,
    "harqErrorRate_3rd_Ul:vector": 0xF8000001,
    "rlcPacketLossD2D:vector": 0xF8000001,
    "rlcPacketLossTotal:vector": 0xF8000001,
    "rlcPduPacketLossD2D:vector": 0xF8000001,
    "queueLength:vector": 0x03010000, # pk
    "queueBitLength:vector": 0x03000000, # b
    "distance:vector": 0x84964924, 
    "incomingPacketLengths:vector": 0x03000000, # b
    "queueingTime:vector": 0x84925924,
    "outgoingPacketLengths:vector": 0x03000000, # b
    "avgServedBlocksUl:vector": 0x03020000, # blocks
    "avgServedBlocksDl:vector": 0x03020000, # blocks
    "measuredSinrUl:vector": 0xF8000000,	
    "measuredSinrDl:vector": 0xF8000000,	
    "alertDelay:vector": 0x84925924,
    "alertRcvdMsg:vector": 0x84925924,
    "averageCqiUl:vector": 0x03030000,
    "rcvdSinrUl:vector": 0xF8000000,
    "macDelayUl:vector": 0x84925924,
    "averageCqiD2D:vector": 0x03030000,
    "macDelayDl:vector": 0x84925924,
    "rlcPduThroughputD2D:vector": 0x03040000, # Bps *8
    "rlcPduDelayD2D:vector": 0x84925924,
    "rlcThroughputD2D:vector": 0x03040000, # Bps *8
    "rlcDelayD2D:vector": 0x84925924,
    "incomingDataRate:vector": 0x03040000, # bps
    "outgoingDataRate:vector": 0x03040000, # bps
}

transformations = { 
    "txPk:vector(packetBytes)": lambda x: x * 8, # bits *8 
    "rxPkOk:vector(packetBytes)": lambda x: x * 8, # bits *8 
    "passedUpPk:vector(packetBytes)": lambda x: x * 8, # bits *8 
    "receivedPacketFromLowerLayer:vector(packetBytes)": lambda x: x * 8, # bits *8 
    "posLongCar:vector": lambda x: x * 3.141592653589793 / 180, # *pi/180 
    "posLatCar:vector": lambda x: x * 3.141592653589793 / 180, # *pi/180 
    "packetSent:vector(packetBytes)": lambda x: x * 8, # bits *8 
    "rcvdPkFromHl:vector(packetBytes)": lambda x: x * 8, # bits *8 
    "receivedPacketFromUpperLayer:vector(packetBytes)": lambda x: x * 8, # bits *8 
    "sentPacketToLowerLayer:vector(packetBytes)": lambda x: x * 8, # bits *8 
    "packetReceived:vector(packetBytes)": lambda x: x * 8, # bits *8 
    "sentPacketToUpperLayer:vector(packetBytes)": lambda x: x * 8, # bits *8 
    "rlcPduThroughputD2D:vector": lambda x: x * 8, # Bps *8 
    "rlcThroughputD2D:vector": lambda x: x * 8
}

modules = ['FiveGWorld.car[0].cellularNic.nrChannelModel[0]', 'FiveGWorld.gNodeB[0].x2ppp[0].queue', 'FiveGWorld.gNodeB[0].x2ppp[0].ppp', 'FiveGWorld.gNodeB[0].x2ppp[1].queue', 'FiveGWorld.gNodeB[0].x2ppp[1].ppp', 'FiveGWorld.gNodeB[1].x2ppp[1].queue', 'FiveGWorld.gNodeB[1].x2ppp[1].ppp', 'FiveGWorld.gNodeB[1].x2ppp[0].queue', 'FiveGWorld.gNodeB[1].x2ppp[0].ppp', 'FiveGWorld.gNodeB[2].x2ppp[1].queue', 'FiveGWorld.gNodeB[2].x2ppp[1].ppp', 'FiveGWorld.gNodeB[2].x2ppp[0].queue', 'FiveGWorld.gNodeB[2].x2ppp[0].ppp', 'FiveGWorld.gNodeB[3].x2ppp[1].queue', 'FiveGWorld.gNodeB[3].x2ppp[1].ppp', 'FiveGWorld.gNodeB[3].x2ppp[0].queue', 'FiveGWorld.gNodeB[3].x2ppp[0].ppp', 'FiveGWorld.gNodeB[4].x2ppp[1].queue', 'FiveGWorld.gNodeB[4].x2ppp[1].ppp', 'FiveGWorld.gNodeB[4].x2ppp[0].queue', 'FiveGWorld.gNodeB[4].x2ppp[0].ppp', 'FiveGWorld.gNodeB[5].x2ppp[1].queue', 'FiveGWorld.gNodeB[5].x2ppp[1].ppp', 'FiveGWorld.gNodeB[5].x2ppp[0].queue', 'FiveGWorld.gNodeB[5].x2ppp[0].ppp', 'FiveGWorld.gNodeB[6].x2ppp[1].queue', 'FiveGWorld.gNodeB[6].x2ppp[1].ppp', 'FiveGWorld.gNodeB[6].x2ppp[0].queue', 'FiveGWorld.gNodeB[6].x2ppp[0].ppp', 'FiveGWorld.gNodeB[7].x2ppp[1].queue', 'FiveGWorld.gNodeB[7].x2ppp[1].ppp', 'FiveGWorld.gNodeB[7].x2ppp[0].queue', 'FiveGWorld.gNodeB[7].x2ppp[0].ppp', 'FiveGWorld.gNodeB[8].x2ppp[1].queue', 'FiveGWorld.gNodeB[8].x2ppp[1].ppp', 'FiveGWorld.gNodeB[8].x2ppp[0].queue', 'FiveGWorld.gNodeB[8].x2ppp[0].ppp', 'FiveGWorld.gNodeB[9].x2ppp[1].queue', 'FiveGWorld.gNodeB[9].x2ppp[1].ppp', 'FiveGWorld.gNodeB[9].x2ppp[0].queue', 'FiveGWorld.gNodeB[9].x2ppp[0].ppp', 'FiveGWorld.gNodeB[10].x2ppp[1].queue', 'FiveGWorld.gNodeB[10].x2ppp[1].ppp', 'FiveGWorld.gNodeB[10].x2ppp[0].queue', 'FiveGWorld.gNodeB[10].x2ppp[0].ppp', 'FiveGWorld.gNodeB[11].x2ppp[1].queue', 'FiveGWorld.gNodeB[11].x2ppp[1].ppp', 'FiveGWorld.gNodeB[11].x2ppp[0].queue', 'FiveGWorld.gNodeB[11].x2ppp[0].ppp', 'FiveGWorld.gNodeB[12].x2ppp[1].queue', 'FiveGWorld.gNodeB[12].x2ppp[1].ppp', 'FiveGWorld.gNodeB[12].x2ppp[0].queue', 'FiveGWorld.gNodeB[12].x2ppp[0].ppp', 'FiveGWorld.gNodeB[13].x2ppp[1].queue', 'FiveGWorld.gNodeB[13].x2ppp[1].ppp', 'FiveGWorld.gNodeB[13].x2ppp[0].queue', 'FiveGWorld.gNodeB[13].x2ppp[0].ppp', 'FiveGWorld.gNodeB[14].x2ppp[1].queue', 'FiveGWorld.gNodeB[14].x2ppp[1].ppp', 'FiveGWorld.gNodeB[14].x2ppp[0].queue', 'FiveGWorld.gNodeB[14].x2ppp[0].ppp', 'FiveGWorld.gNodeB[15].x2ppp[1].queue', 'FiveGWorld.gNodeB[15].x2ppp[1].ppp', 'FiveGWorld.gNodeB[15].x2ppp[0].queue', 'FiveGWorld.gNodeB[15].x2ppp[0].ppp', 'FiveGWorld.gNodeB[16].x2ppp[1].queue', 'FiveGWorld.gNodeB[16].x2ppp[1].ppp', 'FiveGWorld.gNodeB[16].x2ppp[0].queue', 'FiveGWorld.gNodeB[16].x2ppp[0].ppp', 'FiveGWorld.gNodeB[17].x2ppp[1].queue', 'FiveGWorld.gNodeB[17].x2ppp[1].ppp', 'FiveGWorld.gNodeB[17].x2ppp[0].queue', 'FiveGWorld.gNodeB[17].x2ppp[0].ppp', 'FiveGWorld.gNodeB[18].x2ppp[1].queue', 'FiveGWorld.gNodeB[18].x2ppp[1].ppp', 'FiveGWorld.gNodeB[18].x2ppp[0].queue', 'FiveGWorld.gNodeB[18].x2ppp[0].ppp', 'FiveGWorld.gNodeB[19].x2ppp[1].queue', 'FiveGWorld.gNodeB[19].x2ppp[1].ppp', 'FiveGWorld.gNodeB[19].x2ppp[0].queue', 'FiveGWorld.gNodeB[19].x2ppp[0].ppp', 'FiveGWorld.gNodeB[20].x2ppp[1].queue', 'FiveGWorld.gNodeB[20].x2ppp[1].ppp', 'FiveGWorld.gNodeB[20].x2ppp[0].queue', 'FiveGWorld.gNodeB[20].x2ppp[0].ppp', 'FiveGWorld.gNodeB[21].x2ppp[1].queue', 'FiveGWorld.gNodeB[21].x2ppp[1].ppp', 'FiveGWorld.gNodeB[21].x2ppp[0].queue', 'FiveGWorld.gNodeB[21].x2ppp[0].ppp', 'FiveGWorld.gNodeB[22].x2ppp[1].queue', 'FiveGWorld.gNodeB[22].x2ppp[1].ppp', 'FiveGWorld.gNodeB[22].x2ppp[0].queue', 'FiveGWorld.gNodeB[22].x2ppp[0].ppp', 'FiveGWorld.gNodeB[23].x2ppp[1].queue', 'FiveGWorld.gNodeB[23].x2ppp[1].ppp', 'FiveGWorld.gNodeB[23].x2ppp[0].queue', 'FiveGWorld.gNodeB[23].x2ppp[0].ppp', 'FiveGWorld.gNodeB[24].x2ppp[1].queue', 'FiveGWorld.gNodeB[24].x2ppp[1].ppp', 'FiveGWorld.gNodeB[24].x2ppp[0].queue', 'FiveGWorld.gNodeB[24].x2ppp[0].ppp', 'FiveGWorld.gNodeB[25].x2ppp[1].queue', 'FiveGWorld.gNodeB[25].x2ppp[1].ppp', 'FiveGWorld.gNodeB[25].x2ppp[0].queue', 'FiveGWorld.gNodeB[25].x2ppp[0].ppp', 'FiveGWorld.gNodeB[26].x2ppp[1].queue', 'FiveGWorld.gNodeB[26].x2ppp[1].ppp', 'FiveGWorld.gNodeB[26].x2ppp[0].queue', 'FiveGWorld.gNodeB[26].x2ppp[0].ppp', 'FiveGWorld.gNodeB[27].x2ppp[1].queue', 'FiveGWorld.gNodeB[27].x2ppp[1].ppp', 'FiveGWorld.gNodeB[27].x2ppp[0].queue', 'FiveGWorld.gNodeB[27].x2ppp[0].ppp', 'FiveGWorld.gNodeB[28].x2ppp[1].queue', 'FiveGWorld.gNodeB[28].x2ppp[1].ppp', 'FiveGWorld.gNodeB[28].x2ppp[0].queue', 'FiveGWorld.gNodeB[28].x2ppp[0].ppp', 'FiveGWorld.gNodeB[29].x2ppp[1].queue', 'FiveGWorld.gNodeB[29].x2ppp[1].ppp', 'FiveGWorld.gNodeB[29].x2ppp[0].queue', 'FiveGWorld.gNodeB[29].x2ppp[0].ppp', 'FiveGWorld.gNodeB[30].x2ppp[1].queue', 'FiveGWorld.gNodeB[30].x2ppp[1].ppp', 'FiveGWorld.gNodeB[30].x2ppp[0].queue', 'FiveGWorld.gNodeB[30].x2ppp[0].ppp', 'FiveGWorld.gNodeB[31].x2ppp[1].queue', 'FiveGWorld.gNodeB[31].x2ppp[1].ppp', 'FiveGWorld.gNodeB[31].x2ppp[0].queue', 'FiveGWorld.gNodeB[31].x2ppp[0].ppp', 'FiveGWorld.gNodeB[32].x2ppp[1].queue', 'FiveGWorld.gNodeB[32].x2ppp[1].ppp', 'FiveGWorld.gNodeB[32].x2ppp[0].queue', 'FiveGWorld.gNodeB[32].x2ppp[0].ppp', 'FiveGWorld.gNodeB[33].x2ppp[1].queue', 'FiveGWorld.gNodeB[33].x2ppp[1].ppp', 'FiveGWorld.gNodeB[33].x2ppp[0].queue', 'FiveGWorld.gNodeB[33].x2ppp[0].ppp', 'FiveGWorld.gNodeB[34].x2ppp[1].queue', 'FiveGWorld.gNodeB[34].x2ppp[1].ppp', 'FiveGWorld.gNodeB[34].x2ppp[0].queue', 'FiveGWorld.gNodeB[34].x2ppp[0].ppp', 'FiveGWorld.gNodeB[35].x2ppp[1].queue', 'FiveGWorld.gNodeB[35].x2ppp[1].ppp', 'FiveGWorld.gNodeB[35].x2ppp[0].queue', 'FiveGWorld.gNodeB[35].x2ppp[0].ppp', 'FiveGWorld.gNodeB[36].x2ppp[1].queue', 'FiveGWorld.gNodeB[36].x2ppp[1].ppp', 'FiveGWorld.gNodeB[36].x2ppp[0].queue', 'FiveGWorld.gNodeB[36].x2ppp[0].ppp', 'FiveGWorld.gNodeB[37].x2ppp[1].queue', 'FiveGWorld.gNodeB[37].x2ppp[1].ppp', 'FiveGWorld.gNodeB[37].x2ppp[0].queue', 'FiveGWorld.gNodeB[37].x2ppp[0].ppp', 'FiveGWorld.gNodeB[38].x2ppp[1].queue', 'FiveGWorld.gNodeB[38].x2ppp[1].ppp', 'FiveGWorld.gNodeB[38].x2ppp[0].queue', 'FiveGWorld.gNodeB[38].x2ppp[0].ppp', 'FiveGWorld.gNodeB[39].x2ppp[1].queue', 'FiveGWorld.gNodeB[39].x2ppp[1].ppp', 'FiveGWorld.gNodeB[39].x2ppp[0].queue', 'FiveGWorld.gNodeB[39].x2ppp[0].ppp', 'FiveGWorld.gNodeB[40].x2ppp[1].queue', 'FiveGWorld.gNodeB[40].x2ppp[1].ppp', 'FiveGWorld.gNodeB[40].x2ppp[0].queue', 'FiveGWorld.gNodeB[40].x2ppp[0].ppp', 'FiveGWorld.gNodeB[41].x2ppp[1].queue', 'FiveGWorld.gNodeB[41].x2ppp[1].ppp', 'FiveGWorld.gNodeB[41].x2ppp[0].queue', 'FiveGWorld.gNodeB[41].x2ppp[0].ppp', 'FiveGWorld.gNodeB[42].x2ppp[1].queue', 'FiveGWorld.gNodeB[42].x2ppp[1].ppp', 'FiveGWorld.gNodeB[42].x2ppp[0].queue', 'FiveGWorld.gNodeB[42].x2ppp[0].ppp', 'FiveGWorld.gNodeB[43].x2ppp[1].queue', 'FiveGWorld.gNodeB[43].x2ppp[1].ppp', 'FiveGWorld.gNodeB[43].x2ppp[0].queue', 'FiveGWorld.gNodeB[43].x2ppp[0].ppp', 'FiveGWorld.gNodeB[44].x2ppp[1].queue', 'FiveGWorld.gNodeB[44].x2ppp[1].ppp', 'FiveGWorld.gNodeB[44].x2ppp[0].queue', 'FiveGWorld.gNodeB[44].x2ppp[0].ppp', 'FiveGWorld.gNodeB[45].x2ppp[1].queue', 'FiveGWorld.gNodeB[45].x2ppp[1].ppp', 'FiveGWorld.gNodeB[45].x2ppp[0].queue', 'FiveGWorld.gNodeB[45].x2ppp[0].ppp', 'FiveGWorld.gNodeB[46].x2ppp[1].queue', 'FiveGWorld.gNodeB[46].x2ppp[1].ppp', 'FiveGWorld.gNodeB[46].x2ppp[0].queue', 'FiveGWorld.gNodeB[46].x2ppp[0].ppp', 'FiveGWorld.gNodeB[0].cellularNic.mac', 'FiveGWorld.gNodeB[1].cellularNic.mac', 'FiveGWorld.gNodeB[2].cellularNic.mac', 'FiveGWorld.gNodeB[3].cellularNic.mac', 'FiveGWorld.gNodeB[4].cellularNic.mac', 'FiveGWorld.gNodeB[5].cellularNic.mac', 'FiveGWorld.gNodeB[6].cellularNic.mac', 'FiveGWorld.gNodeB[7].cellularNic.mac', 'FiveGWorld.gNodeB[8].cellularNic.mac', 'FiveGWorld.gNodeB[9].cellularNic.mac', 'FiveGWorld.gNodeB[10].cellularNic.mac', 'FiveGWorld.gNodeB[11].cellularNic.mac', 'FiveGWorld.gNodeB[12].cellularNic.mac', 'FiveGWorld.gNodeB[13].cellularNic.mac', 'FiveGWorld.gNodeB[14].cellularNic.mac', 'FiveGWorld.gNodeB[15].cellularNic.mac', 'FiveGWorld.gNodeB[16].cellularNic.mac', 'FiveGWorld.gNodeB[17].cellularNic.mac', 'FiveGWorld.gNodeB[18].cellularNic.mac', 'FiveGWorld.gNodeB[19].cellularNic.mac', 'FiveGWorld.gNodeB[20].cellularNic.mac', 'FiveGWorld.gNodeB[21].cellularNic.mac', 'FiveGWorld.gNodeB[22].cellularNic.mac', 'FiveGWorld.gNodeB[23].cellularNic.mac', 'FiveGWorld.gNodeB[24].cellularNic.mac', 'FiveGWorld.gNodeB[25].cellularNic.mac', 'FiveGWorld.gNodeB[26].cellularNic.mac', 'FiveGWorld.gNodeB[27].cellularNic.mac', 'FiveGWorld.gNodeB[28].cellularNic.mac', 'FiveGWorld.gNodeB[29].cellularNic.mac', 'FiveGWorld.gNodeB[30].cellularNic.mac', 'FiveGWorld.gNodeB[31].cellularNic.mac', 'FiveGWorld.gNodeB[32].cellularNic.mac', 'FiveGWorld.gNodeB[33].cellularNic.mac', 'FiveGWorld.gNodeB[34].cellularNic.mac', 'FiveGWorld.gNodeB[35].cellularNic.mac', 'FiveGWorld.gNodeB[36].cellularNic.mac', 'FiveGWorld.gNodeB[37].cellularNic.mac', 'FiveGWorld.gNodeB[38].cellularNic.mac', 'FiveGWorld.gNodeB[39].cellularNic.mac', 'FiveGWorld.gNodeB[40].cellularNic.mac', 'FiveGWorld.gNodeB[41].cellularNic.mac', 'FiveGWorld.gNodeB[42].cellularNic.mac', 'FiveGWorld.gNodeB[43].cellularNic.mac', 'FiveGWorld.gNodeB[44].cellularNic.mac', 'FiveGWorld.gNodeB[45].cellularNic.mac', 'FiveGWorld.gNodeB[46].cellularNic.mac', 'FiveGWorld.car[0].mobility', 'FiveGWorld.car[0].udp', 'FiveGWorld.car[0].lo[0].lo', 'FiveGWorld.car[0].cellularNic.pdcpRrc', 'FiveGWorld.car[0].cellularNic.nrRlc.um', 'FiveGWorld.car[0].app[1]', 'FiveGWorld.car[0].cellularNic.nrMac', 'FiveGWorld.car[0].cellularNic.nrPhy', 'FiveGWorld.car[1].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[1].mobility', 'FiveGWorld.car[1].udp', 'FiveGWorld.car[1].lo[0].lo', 'FiveGWorld.car[1].cellularNic.pdcpRrc', 'FiveGWorld.car[1].cellularNic.nrRlc.um', 'FiveGWorld.car[1].app[1]', 'FiveGWorld.car[1].cellularNic.nrMac', 'FiveGWorld.car[1].cellularNic.nrPhy', 'FiveGWorld.car[2].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[2].mobility', 'FiveGWorld.car[2].udp', 'FiveGWorld.car[2].lo[0].lo', 'FiveGWorld.car[2].cellularNic.pdcpRrc', 'FiveGWorld.car[2].cellularNic.nrRlc.um', 'FiveGWorld.car[2].app[1]', 'FiveGWorld.car[2].cellularNic.nrMac', 'FiveGWorld.car[2].cellularNic.nrPhy', 'FiveGWorld.car[3].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[3].mobility', 'FiveGWorld.car[3].app[1]', 'FiveGWorld.car[3].udp', 'FiveGWorld.car[3].lo[0].lo', 'FiveGWorld.car[3].cellularNic.pdcpRrc', 'FiveGWorld.car[3].cellularNic.nrRlc.um', 'FiveGWorld.car[3].cellularNic.nrMac', 'FiveGWorld.car[3].cellularNic.nrPhy', 'FiveGWorld.car[4].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[4].mobility', 'FiveGWorld.car[4].udp', 'FiveGWorld.car[4].lo[0].lo', 'FiveGWorld.car[4].cellularNic.pdcpRrc', 'FiveGWorld.car[4].cellularNic.nrRlc.um', 'FiveGWorld.car[4].app[1]', 'FiveGWorld.car[4].cellularNic.nrMac', 'FiveGWorld.car[4].cellularNic.nrPhy', 'FiveGWorld.car[5].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[5].mobility', 'FiveGWorld.car[5].udp', 'FiveGWorld.car[5].lo[0].lo', 'FiveGWorld.car[5].cellularNic.pdcpRrc', 'FiveGWorld.car[5].cellularNic.nrRlc.um', 'FiveGWorld.car[5].app[1]', 'FiveGWorld.car[5].cellularNic.nrMac', 'FiveGWorld.car[5].cellularNic.nrPhy', 'FiveGWorld.car[6].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[6].mobility', 'FiveGWorld.car[6].udp', 'FiveGWorld.car[6].lo[0].lo', 'FiveGWorld.car[6].cellularNic.pdcpRrc', 'FiveGWorld.car[6].cellularNic.nrRlc.um', 'FiveGWorld.car[6].app[1]', 'FiveGWorld.car[6].cellularNic.nrMac', 'FiveGWorld.car[6].cellularNic.nrPhy', 'FiveGWorld.car[7].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[7].mobility', 'FiveGWorld.car[7].udp', 'FiveGWorld.car[7].lo[0].lo', 'FiveGWorld.car[7].cellularNic.pdcpRrc', 'FiveGWorld.car[7].cellularNic.nrRlc.um', 'FiveGWorld.car[7].app[1]', 'FiveGWorld.car[7].cellularNic.nrMac', 'FiveGWorld.car[7].cellularNic.nrPhy', 'FiveGWorld.car[8].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[8].mobility', 'FiveGWorld.car[8].udp', 'FiveGWorld.car[8].lo[0].lo', 'FiveGWorld.car[8].app[1]', 'FiveGWorld.car[8].cellularNic.pdcpRrc', 'FiveGWorld.car[8].cellularNic.nrRlc.um', 'FiveGWorld.car[8].cellularNic.nrMac', 'FiveGWorld.car[8].cellularNic.nrPhy', 'FiveGWorld.car[9].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[9].app[1]', 'FiveGWorld.car[9].mobility', 'FiveGWorld.car[9].udp', 'FiveGWorld.car[9].lo[0].lo', 'FiveGWorld.car[9].cellularNic.pdcpRrc', 'FiveGWorld.car[9].cellularNic.nrRlc.um', 'FiveGWorld.car[9].cellularNic.nrMac', 'FiveGWorld.car[9].cellularNic.nrPhy', 'FiveGWorld.car[10].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[10].mobility', 'FiveGWorld.car[10].udp', 'FiveGWorld.car[10].lo[0].lo', 'FiveGWorld.car[10].cellularNic.pdcpRrc', 'FiveGWorld.car[10].cellularNic.nrRlc.um', 'FiveGWorld.car[10].app[1]', 'FiveGWorld.car[10].cellularNic.nrMac', 'FiveGWorld.car[10].cellularNic.nrPhy', 'FiveGWorld.car[11].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[11].mobility', 'FiveGWorld.car[11].udp', 'FiveGWorld.car[11].lo[0].lo', 'FiveGWorld.car[11].cellularNic.pdcpRrc', 'FiveGWorld.car[11].cellularNic.nrRlc.um', 'FiveGWorld.car[11].app[1]', 'FiveGWorld.car[11].cellularNic.nrMac', 'FiveGWorld.car[11].cellularNic.nrPhy', 'FiveGWorld.car[12].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[12].mobility', 'FiveGWorld.car[12].udp', 'FiveGWorld.car[12].lo[0].lo', 'FiveGWorld.car[12].cellularNic.pdcpRrc', 'FiveGWorld.car[12].cellularNic.nrRlc.um', 'FiveGWorld.car[12].app[1]', 'FiveGWorld.car[12].cellularNic.nrMac', 'FiveGWorld.car[12].cellularNic.nrPhy', 'FiveGWorld.car[13].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[13].mobility', 'FiveGWorld.car[13].app[1]', 'FiveGWorld.car[13].udp', 'FiveGWorld.car[13].lo[0].lo', 'FiveGWorld.car[13].cellularNic.pdcpRrc', 'FiveGWorld.car[13].cellularNic.nrRlc.um', 'FiveGWorld.car[13].cellularNic.nrMac', 'FiveGWorld.car[13].cellularNic.nrPhy', 'FiveGWorld.car[14].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[14].mobility', 'FiveGWorld.car[14].udp', 'FiveGWorld.car[14].lo[0].lo', 'FiveGWorld.car[14].cellularNic.pdcpRrc', 'FiveGWorld.car[14].cellularNic.nrRlc.um', 'FiveGWorld.car[14].app[1]', 'FiveGWorld.car[14].cellularNic.nrMac', 'FiveGWorld.car[14].cellularNic.nrPhy', 'FiveGWorld.car[15].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[15].mobility', 'FiveGWorld.car[15].udp', 'FiveGWorld.car[15].lo[0].lo', 'FiveGWorld.car[15].cellularNic.pdcpRrc', 'FiveGWorld.car[15].cellularNic.nrRlc.um', 'FiveGWorld.car[15].app[1]', 'FiveGWorld.car[15].cellularNic.nrMac', 'FiveGWorld.car[15].cellularNic.nrPhy', 'FiveGWorld.car[16].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[16].mobility', 'FiveGWorld.car[16].udp', 'FiveGWorld.car[16].lo[0].lo', 'FiveGWorld.car[16].cellularNic.pdcpRrc', 'FiveGWorld.car[16].cellularNic.nrRlc.um', 'FiveGWorld.car[16].app[1]', 'FiveGWorld.car[16].cellularNic.nrMac', 'FiveGWorld.car[16].cellularNic.nrPhy', 'FiveGWorld.car[17].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[17].mobility', 'FiveGWorld.car[17].udp', 'FiveGWorld.car[17].lo[0].lo', 'FiveGWorld.car[17].cellularNic.pdcpRrc', 'FiveGWorld.car[17].cellularNic.nrRlc.um', 'FiveGWorld.car[17].app[1]', 'FiveGWorld.car[17].cellularNic.nrMac', 'FiveGWorld.car[17].cellularNic.nrPhy', 'FiveGWorld.car[18].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[18].mobility', 'FiveGWorld.car[18].udp', 'FiveGWorld.car[18].lo[0].lo', 'FiveGWorld.car[18].cellularNic.pdcpRrc', 'FiveGWorld.car[18].cellularNic.nrRlc.um', 'FiveGWorld.car[18].app[1]', 'FiveGWorld.car[18].cellularNic.nrMac', 'FiveGWorld.car[18].cellularNic.nrPhy', 'FiveGWorld.car[19].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[19].mobility', 'FiveGWorld.car[19].udp', 'FiveGWorld.car[19].lo[0].lo', 'FiveGWorld.car[19].cellularNic.pdcpRrc', 'FiveGWorld.car[19].cellularNic.nrRlc.um', 'FiveGWorld.car[19].app[1]', 'FiveGWorld.car[19].cellularNic.nrMac', 'FiveGWorld.car[19].cellularNic.nrPhy', 'FiveGWorld.car[20].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[20].mobility', 'FiveGWorld.car[21].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[21].mobility', 'FiveGWorld.car[20].udp', 'FiveGWorld.car[20].lo[0].lo', 'FiveGWorld.car[20].cellularNic.pdcpRrc', 'FiveGWorld.car[20].cellularNic.nrRlc.um', 'FiveGWorld.car[20].app[1]', 'FiveGWorld.car[20].cellularNic.nrMac', 'FiveGWorld.car[20].cellularNic.nrPhy', 'FiveGWorld.car[21].udp', 'FiveGWorld.car[21].lo[0].lo', 'FiveGWorld.car[21].cellularNic.pdcpRrc', 'FiveGWorld.car[21].cellularNic.nrRlc.um', 'FiveGWorld.car[21].app[1]', 'FiveGWorld.car[21].cellularNic.nrMac', 'FiveGWorld.car[21].cellularNic.nrPhy', 'FiveGWorld.car[22].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[22].mobility', 'FiveGWorld.car[22].app[1]', 'FiveGWorld.car[22].udp', 'FiveGWorld.car[22].lo[0].lo', 'FiveGWorld.car[22].cellularNic.pdcpRrc', 'FiveGWorld.car[22].cellularNic.nrRlc.um', 'FiveGWorld.car[22].cellularNic.nrMac', 'FiveGWorld.car[22].cellularNic.nrPhy', 'FiveGWorld.car[23].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[23].mobility', 'FiveGWorld.car[23].udp', 'FiveGWorld.car[23].lo[0].lo', 'FiveGWorld.car[23].cellularNic.pdcpRrc', 'FiveGWorld.car[23].cellularNic.nrRlc.um', 'FiveGWorld.car[23].app[1]', 'FiveGWorld.car[23].cellularNic.nrMac', 'FiveGWorld.car[23].cellularNic.nrPhy', 'FiveGWorld.car[24].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[24].app[1]', 'FiveGWorld.car[24].mobility', 'FiveGWorld.car[24].udp', 'FiveGWorld.car[24].lo[0].lo', 'FiveGWorld.car[24].cellularNic.pdcpRrc', 'FiveGWorld.car[24].cellularNic.nrRlc.um', 'FiveGWorld.car[24].cellularNic.nrMac', 'FiveGWorld.car[24].cellularNic.nrPhy', 'FiveGWorld.car[25].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[25].mobility', 'FiveGWorld.car[25].udp', 'FiveGWorld.car[25].lo[0].lo', 'FiveGWorld.car[25].cellularNic.pdcpRrc', 'FiveGWorld.car[25].cellularNic.nrRlc.um', 'FiveGWorld.car[25].app[1]', 'FiveGWorld.car[25].cellularNic.nrMac', 'FiveGWorld.car[25].cellularNic.nrPhy', 'FiveGWorld.car[26].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[26].mobility', 'FiveGWorld.car[26].udp', 'FiveGWorld.car[26].lo[0].lo', 'FiveGWorld.car[26].cellularNic.pdcpRrc', 'FiveGWorld.car[26].cellularNic.nrRlc.um', 'FiveGWorld.car[26].app[1]', 'FiveGWorld.car[26].cellularNic.nrMac', 'FiveGWorld.car[26].cellularNic.nrPhy', 'FiveGWorld.car[27].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[27].mobility', 'FiveGWorld.car[27].udp', 'FiveGWorld.car[27].lo[0].lo', 'FiveGWorld.car[27].cellularNic.pdcpRrc', 'FiveGWorld.car[27].cellularNic.nrRlc.um', 'FiveGWorld.car[27].app[1]', 'FiveGWorld.car[27].cellularNic.nrMac', 'FiveGWorld.car[27].cellularNic.nrPhy', 'FiveGWorld.car[28].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[28].mobility', 'FiveGWorld.car[28].udp', 'FiveGWorld.car[28].lo[0].lo', 'FiveGWorld.car[28].cellularNic.pdcpRrc', 'FiveGWorld.car[28].cellularNic.nrRlc.um', 'FiveGWorld.car[28].app[1]', 'FiveGWorld.car[28].cellularNic.nrMac', 'FiveGWorld.car[28].cellularNic.nrPhy', 'FiveGWorld.car[29].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[29].app[1]', 'FiveGWorld.car[29].mobility', 'FiveGWorld.car[29].udp', 'FiveGWorld.car[29].lo[0].lo', 'FiveGWorld.car[29].cellularNic.pdcpRrc', 'FiveGWorld.car[29].cellularNic.nrRlc.um', 'FiveGWorld.car[29].cellularNic.nrMac', 'FiveGWorld.car[29].cellularNic.nrPhy', 'FiveGWorld.car[30].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[30].mobility', 'FiveGWorld.car[30].udp', 'FiveGWorld.car[30].lo[0].lo', 'FiveGWorld.car[30].cellularNic.pdcpRrc', 'FiveGWorld.car[30].cellularNic.nrRlc.um', 'FiveGWorld.car[30].app[1]', 'FiveGWorld.car[30].cellularNic.nrMac', 'FiveGWorld.car[30].cellularNic.nrPhy', 'FiveGWorld.car[31].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[31].mobility', 'FiveGWorld.car[31].udp', 'FiveGWorld.car[31].lo[0].lo', 'FiveGWorld.car[31].cellularNic.pdcpRrc', 'FiveGWorld.car[31].cellularNic.nrRlc.um', 'FiveGWorld.car[31].app[1]', 'FiveGWorld.car[31].cellularNic.nrMac', 'FiveGWorld.car[31].cellularNic.nrPhy', 'FiveGWorld.car[32].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[32].mobility', 'FiveGWorld.car[32].udp', 'FiveGWorld.car[32].lo[0].lo', 'FiveGWorld.car[32].cellularNic.pdcpRrc', 'FiveGWorld.car[32].cellularNic.nrRlc.um', 'FiveGWorld.car[32].app[1]', 'FiveGWorld.car[32].cellularNic.nrMac', 'FiveGWorld.car[32].cellularNic.nrPhy', 'FiveGWorld.car[33].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[33].mobility', 'FiveGWorld.car[33].udp', 'FiveGWorld.car[33].lo[0].lo', 'FiveGWorld.car[33].cellularNic.pdcpRrc', 'FiveGWorld.car[33].cellularNic.nrRlc.um', 'FiveGWorld.car[33].app[1]', 'FiveGWorld.car[33].cellularNic.nrMac', 'FiveGWorld.car[33].cellularNic.nrPhy', 'FiveGWorld.car[34].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[34].mobility', 'FiveGWorld.car[34].udp', 'FiveGWorld.car[34].lo[0].lo', 'FiveGWorld.car[34].cellularNic.pdcpRrc', 'FiveGWorld.car[34].cellularNic.nrRlc.um', 'FiveGWorld.car[34].app[1]', 'FiveGWorld.car[34].cellularNic.nrMac', 'FiveGWorld.car[34].cellularNic.nrPhy', 'FiveGWorld.car[35].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[35].mobility', 'FiveGWorld.car[35].udp', 'FiveGWorld.car[35].lo[0].lo', 'FiveGWorld.car[35].cellularNic.pdcpRrc', 'FiveGWorld.car[35].cellularNic.nrRlc.um', 'FiveGWorld.car[35].app[1]', 'FiveGWorld.car[35].cellularNic.nrMac', 'FiveGWorld.car[35].cellularNic.nrPhy', 'FiveGWorld.car[36].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[36].mobility', 'FiveGWorld.car[36].udp', 'FiveGWorld.car[36].lo[0].lo', 'FiveGWorld.car[36].cellularNic.pdcpRrc', 'FiveGWorld.car[36].cellularNic.nrRlc.um', 'FiveGWorld.car[36].app[1]', 'FiveGWorld.car[36].cellularNic.nrMac', 'FiveGWorld.car[36].cellularNic.nrPhy', 'FiveGWorld.car[37].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[37].mobility', 'FiveGWorld.car[37].udp', 'FiveGWorld.car[37].lo[0].lo', 'FiveGWorld.car[37].cellularNic.pdcpRrc', 'FiveGWorld.car[37].cellularNic.nrRlc.um', 'FiveGWorld.car[37].app[1]', 'FiveGWorld.car[37].cellularNic.nrMac', 'FiveGWorld.car[37].cellularNic.nrPhy', 'FiveGWorld.car[38].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[38].mobility', 'FiveGWorld.car[38].udp', 'FiveGWorld.car[38].lo[0].lo', 'FiveGWorld.car[38].cellularNic.pdcpRrc', 'FiveGWorld.car[38].cellularNic.nrRlc.um', 'FiveGWorld.car[38].app[1]', 'FiveGWorld.car[38].cellularNic.nrMac', 'FiveGWorld.car[38].cellularNic.nrPhy', 'FiveGWorld.car[39].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[39].mobility', 'FiveGWorld.car[39].udp', 'FiveGWorld.car[39].lo[0].lo', 'FiveGWorld.car[39].cellularNic.pdcpRrc', 'FiveGWorld.car[39].cellularNic.nrRlc.um', 'FiveGWorld.car[39].app[1]', 'FiveGWorld.car[39].cellularNic.nrMac', 'FiveGWorld.car[39].cellularNic.nrPhy', 'FiveGWorld.car[40].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[40].mobility', 'FiveGWorld.car[40].udp', 'FiveGWorld.car[40].lo[0].lo', 'FiveGWorld.car[40].cellularNic.pdcpRrc', 'FiveGWorld.car[40].cellularNic.nrRlc.um', 'FiveGWorld.car[40].app[1]', 'FiveGWorld.car[40].cellularNic.nrMac', 'FiveGWorld.car[40].cellularNic.nrPhy', 'FiveGWorld.car[41].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[41].app[1]', 'FiveGWorld.car[41].mobility', 'FiveGWorld.car[41].udp', 'FiveGWorld.car[41].lo[0].lo', 'FiveGWorld.car[41].cellularNic.pdcpRrc', 'FiveGWorld.car[41].cellularNic.nrRlc.um', 'FiveGWorld.car[41].cellularNic.nrMac', 'FiveGWorld.car[41].cellularNic.nrPhy', 'FiveGWorld.car[42].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[42].mobility', 'FiveGWorld.car[43].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[42].udp', 'FiveGWorld.car[42].lo[0].lo', 'FiveGWorld.car[42].cellularNic.pdcpRrc', 'FiveGWorld.car[42].cellularNic.nrRlc.um', 'FiveGWorld.car[42].app[1]', 'FiveGWorld.car[42].cellularNic.nrMac', 'FiveGWorld.car[42].cellularNic.nrPhy', 'FiveGWorld.car[43].mobility', 'FiveGWorld.car[43].udp', 'FiveGWorld.car[43].lo[0].lo', 'FiveGWorld.car[43].cellularNic.pdcpRrc', 'FiveGWorld.car[43].cellularNic.nrRlc.um', 'FiveGWorld.car[43].app[1]', 'FiveGWorld.car[43].cellularNic.nrMac', 'FiveGWorld.car[43].cellularNic.nrPhy', 'FiveGWorld.car[44].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[44].mobility', 'FiveGWorld.car[44].udp', 'FiveGWorld.car[44].lo[0].lo', 'FiveGWorld.car[44].cellularNic.pdcpRrc', 'FiveGWorld.car[44].cellularNic.nrRlc.um', 'FiveGWorld.car[44].app[1]', 'FiveGWorld.car[44].cellularNic.nrMac', 'FiveGWorld.car[44].cellularNic.nrPhy', 'FiveGWorld.car[45].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[45].mobility', 'FiveGWorld.car[45].udp', 'FiveGWorld.car[45].lo[0].lo', 'FiveGWorld.car[45].cellularNic.pdcpRrc', 'FiveGWorld.car[45].cellularNic.nrRlc.um', 'FiveGWorld.car[45].app[1]', 'FiveGWorld.car[45].cellularNic.nrMac', 'FiveGWorld.car[45].cellularNic.nrPhy', 'FiveGWorld.car[46].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[46].mobility', 'FiveGWorld.car[46].udp', 'FiveGWorld.car[46].lo[0].lo', 'FiveGWorld.car[46].cellularNic.pdcpRrc', 'FiveGWorld.car[46].cellularNic.nrRlc.um', 'FiveGWorld.car[46].app[1]', 'FiveGWorld.car[46].cellularNic.nrMac', 'FiveGWorld.car[46].cellularNic.nrPhy', 'FiveGWorld.car[47].cellularNic.nrChannelModel[0]', 'FiveGWorld.car[47].mobility', 'FiveGWorld.car[47].udp', 'FiveGWorld.car[47].lo[0].lo', 'FiveGWorld.car[47].cellularNic.pdcpRrc', 'FiveGWorld.car[47].cellularNic.nrRlc.um', 'FiveGWorld.car[47].app[1]', 'FiveGWorld.car[47].cellularNic.nrMac', 'FiveGWorld.car[47].cellularNic.nrPhy', 'FiveGWorld.car[48].cellularNic.nrChannelModel[0]', 'FiveGWorld.gNodeB[0].pppIf.queue', 'FiveGWorld.gNodeB[0].pppMEHostIf.queue', 'FiveGWorld.gNodeB[1].pppIf.queue', 'FiveGWorld.gNodeB[1].pppMEHostIf.queue', 'FiveGWorld.gNodeB[2].pppIf.queue', 'FiveGWorld.gNodeB[2].pppMEHostIf.queue', 'FiveGWorld.gNodeB[3].pppIf.queue', 'FiveGWorld.gNodeB[3].pppMEHostIf.queue', 'FiveGWorld.gNodeB[4].pppIf.queue', 'FiveGWorld.gNodeB[4].pppMEHostIf.queue', 'FiveGWorld.gNodeB[5].pppIf.queue', 'FiveGWorld.gNodeB[5].pppMEHostIf.queue', 'FiveGWorld.gNodeB[6].pppIf.queue', 'FiveGWorld.gNodeB[6].pppMEHostIf.queue', 'FiveGWorld.gNodeB[7].pppIf.queue', 'FiveGWorld.gNodeB[7].pppMEHostIf.queue', 'FiveGWorld.gNodeB[8].pppIf.queue', 'FiveGWorld.gNodeB[8].pppMEHostIf.queue', 'FiveGWorld.gNodeB[9].pppIf.queue', 'FiveGWorld.gNodeB[9].pppMEHostIf.queue', 'FiveGWorld.gNodeB[10].pppIf.queue', 'FiveGWorld.gNodeB[10].pppMEHostIf.queue', 'FiveGWorld.gNodeB[11].pppIf.queue', 'FiveGWorld.gNodeB[11].pppMEHostIf.queue', 'FiveGWorld.gNodeB[12].pppIf.queue', 'FiveGWorld.gNodeB[12].pppMEHostIf.queue', 'FiveGWorld.gNodeB[13].pppIf.queue', 'FiveGWorld.gNodeB[13].pppMEHostIf.queue', 'FiveGWorld.gNodeB[14].pppIf.queue', 'FiveGWorld.gNodeB[14].pppMEHostIf.queue', 'FiveGWorld.gNodeB[15].pppIf.queue', 'FiveGWorld.gNodeB[15].pppMEHostIf.queue', 'FiveGWorld.gNodeB[16].pppIf.queue', 'FiveGWorld.gNodeB[16].pppMEHostIf.queue', 'FiveGWorld.gNodeB[17].pppIf.queue', 'FiveGWorld.gNodeB[17].pppMEHostIf.queue', 'FiveGWorld.gNodeB[18].pppIf.queue', 'FiveGWorld.gNodeB[18].pppMEHostIf.queue', 'FiveGWorld.gNodeB[19].pppIf.queue', 'FiveGWorld.gNodeB[19].pppMEHostIf.queue', 'FiveGWorld.gNodeB[20].pppIf.queue', 'FiveGWorld.gNodeB[20].pppMEHostIf.queue', 'FiveGWorld.gNodeB[21].pppIf.queue', 'FiveGWorld.gNodeB[21].pppMEHostIf.queue', 'FiveGWorld.gNodeB[22].pppIf.queue', 'FiveGWorld.gNodeB[22].pppMEHostIf.queue', 'FiveGWorld.gNodeB[23].pppIf.queue', 'FiveGWorld.gNodeB[23].pppMEHostIf.queue', 'FiveGWorld.gNodeB[24].pppIf.queue', 'FiveGWorld.gNodeB[24].pppMEHostIf.queue', 'FiveGWorld.gNodeB[25].pppIf.queue', 'FiveGWorld.gNodeB[25].pppMEHostIf.queue', 'FiveGWorld.gNodeB[26].pppIf.queue', 'FiveGWorld.gNodeB[26].pppMEHostIf.queue', 'FiveGWorld.gNodeB[27].pppIf.queue', 'FiveGWorld.gNodeB[27].pppMEHostIf.queue', 'FiveGWorld.gNodeB[28].pppIf.queue', 'FiveGWorld.gNodeB[28].pppMEHostIf.queue', 'FiveGWorld.gNodeB[29].pppIf.queue', 'FiveGWorld.gNodeB[29].pppMEHostIf.queue', 'FiveGWorld.gNodeB[30].pppIf.queue', 'FiveGWorld.gNodeB[30].pppMEHostIf.queue', 'FiveGWorld.gNodeB[31].pppIf.queue', 'FiveGWorld.gNodeB[31].pppMEHostIf.queue', 'FiveGWorld.gNodeB[32].pppIf.queue', 'FiveGWorld.gNodeB[32].pppMEHostIf.queue', 'FiveGWorld.gNodeB[33].pppIf.queue', 'FiveGWorld.gNodeB[33].pppMEHostIf.queue', 'FiveGWorld.gNodeB[34].pppIf.queue', 'FiveGWorld.gNodeB[34].pppMEHostIf.queue', 'FiveGWorld.gNodeB[35].pppIf.queue', 'FiveGWorld.gNodeB[35].pppMEHostIf.queue', 'FiveGWorld.gNodeB[36].pppIf.queue', 'FiveGWorld.gNodeB[36].pppMEHostIf.queue', 'FiveGWorld.gNodeB[37].pppIf.queue', 'FiveGWorld.gNodeB[37].pppMEHostIf.queue', 'FiveGWorld.gNodeB[38].pppIf.queue', 'FiveGWorld.gNodeB[38].pppMEHostIf.queue', 'FiveGWorld.gNodeB[39].pppIf.queue', 'FiveGWorld.gNodeB[39].pppMEHostIf.queue', 'FiveGWorld.gNodeB[40].pppIf.queue', 'FiveGWorld.gNodeB[40].pppMEHostIf.queue', 'FiveGWorld.gNodeB[41].pppIf.queue', 'FiveGWorld.gNodeB[41].pppMEHostIf.queue', 'FiveGWorld.gNodeB[42].pppIf.queue', 'FiveGWorld.gNodeB[42].pppMEHostIf.queue', 'FiveGWorld.gNodeB[43].pppIf.queue', 'FiveGWorld.gNodeB[43].pppMEHostIf.queue', 'FiveGWorld.gNodeB[44].pppIf.queue', 'FiveGWorld.gNodeB[44].pppMEHostIf.queue', 'FiveGWorld.gNodeB[45].pppIf.queue', 'FiveGWorld.gNodeB[45].pppMEHostIf.queue', 'FiveGWorld.gNodeB[46].pppIf.queue', 'FiveGWorld.gNodeB[46].pppMEHostIf.queue']

def extract_integer(x):
    match = re.search(r'car\[(\d+)\]', x)
    if match:
      return int(match.group(1))
    else:
      return None  # Handle cases where the pattern is not found

def get_vehicle_positions_mapping(csv_file_path):
    
    # Load the CSV file
    data = pd.read_csv(csv_file_path)

    # Get the rows with 'name' equal to 'posLatCar:vector' or 'posLongCar:vector'
    pos_data = data[data['name'].isin(['posLatCar:vector', 'posLongCar:vector'])]


    # Get the integer which is within the brackets in the substring 'car[integer]' from the 'module' column 
    pos_data['vehicle'] = pos_data['module'].apply(extract_integer)

    #print(pos_data.head())
    # Create a dictionary with the mapping of the vehicle latitude and longitude and their respective 'vecvalue' column
    pos_mapping = {}
    for _, row in pos_data.iterrows():
        # Create the key with only the vehicle number
        key = f"car{row['vehicle']}"
        if key not in pos_mapping:
            pos_mapping[key] = {}
        # Add the latitude and longitude to the dictionary
        pos_mapping[key][row['name']] = [float(x) for x in row['vecvalue'].split()] if isinstance(row['vecvalue'], str) else [float(row)['vecvalue']]

    return pos_mapping





DATE_TIME_START = '2024-12-20 00:00:00'

import datetime

# Function to convert timestamp to UNIX epoch microseconds
def to_unix_microseconds(seconds):

    # Convert to unix epoch microseconds based on DATE_TIME_START by adding the seconds to the start date
    return int((datetime.datetime.strptime(DATE_TIME_START, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(seconds=float(seconds))).timestamp() * 1000000)
    
# Example usage
print(to_unix_microseconds('0'))

import pyproj

def latlon_to_ecef(lat, lon, height=0):
  """
  Converts latitude and longitude coordinates to Earth-Centered, Earth-Fixed (ECEF) coordinates.

  Args:
    lat: Latitude in degrees.
    lon: Longitude in degrees.
    height: Height above the ellipsoid in meters (default: 0).

  Returns:
    A tuple containing the ECEF X, Y, and Z coordinates in meters.
  """

  wgs84_to_ecef = pyproj.Transformer.from_crs(
      {"proj":'latlong', "ellps":'WGS84', "datum":'WGS84'},
      {"proj":'geocent', "ellps":'WGS84', "datum":'WGS84'},
  )

  ecef_x, ecef_y, ecef_z = wgs84_to_ecef.transform(lon, lat, height) 
  return ecef_x, ecef_y, ecef_z


# Function to generate smartdata structure in batches and save incrementally
def generate_smartdata_in_batches(csv_file_path, output_dir, chunk_size=1):
    os.makedirs(output_dir, exist_ok=True)

    # Get the vehicle positions mapping
    pos_mapping = get_vehicle_positions_mapping(csv_file_path)
    #print(pos_mapping)

    batch_index = 0
    for chunk in pd.read_csv(csv_file_path, chunksize=chunk_size):
        smartdata_dict = {}

        for _, row in chunk.iterrows():
            module = str(row['module'])
            
            # If the module contains 'car', get the vehicle number
            if 'car' in module:
                vehicle = extract_integer(module)
                if vehicle is not None:
                    # Get the latitude and longitude of the vehicle
                    lat, lon = pos_mapping[f"car{vehicle}"]['posLatCar:vector'][0], pos_mapping[f"car{vehicle}"]['posLongCar:vector'][0]
                    # Convert the latitude and longitude to ECEF coordinates
                    x, y, z = latlon_to_ecef(lat, lon) # lat, lon, 0 # 
            else:
                x, y, z = 0, 0, 0

            name = row['name']

            vectime = row['vectime'].split() if isinstance(row['vectime'], str) else [row['vectime']]
            vecvalue = row['vecvalue'].split() if isinstance(row['vecvalue'], str) else [row['vecvalue']]

            unit = mapping.get(name, None)
            if unit is None:
                print(f"Skipping unknown variable: {name}")
                continue

            dev_index = list(mapping.keys()).index(name)
            key = f"{module}_{name}"

            if key not in smartdata_dict:
                smartdata_dict[key] = []
            #print(vectime)
            for ts, value in zip(vectime, vecvalue):
                smartdata = {'smartdata': [
                    {
                    'version': '1.2',
                    'unit': int(hex(unit), 16),
                    'value': float(value) if name not in transformations else transformations[name](float(value)),
                    #'error': 0,
                    #'confidence': 0,
                    'x': x,
                    'y': y,
                    'z': z,
                    't': to_unix_microseconds(ts),
                    'dev': dev_index,
                    'signature': modules.index(module),
                    #'workflow': 0,
                    }
                ]
                }
                    
                smartdata_dict[key].append(smartdata)

            
        
            # Create the series for the batch
            series = { 'series' : {
                    'version' : '1.2',
                    'unit' : int(hex(unit), 16),
                    'x' : 0,
                    'y' : 0,
                    'z' : 0,
                    'r' : 0,
                    't0' : to_unix_microseconds(vectime[0]),
                    't1' : to_unix_microseconds(vectime[-1]),
                    #'workflow' : 0,
                    'dev' : dev_index,
                    'signature' : smartdata_dict[key][0]['smartdata'][0]['signature'],
                }
            }

            # Send to the platform
            #if batch_index == 1:
            send_to_iot_platform(series, smartdata_dict[key])

        output_path = os.path.join(output_dir, f"smartdata_batch_{batch_index}.json")
        with open(output_path, 'w') as f:
            json.dump(smartdata_dict, f)
        print(f"Saved batch {batch_index} to {output_path}")

        batch_index += 1
        #if batch_index >= 2:
        #break

def send_to_iot(url, content, MY_CERTIFICATE):
    session = requests.Session()
    session.headers = {'Content-type' : 'application/json'}
    session.cert = MY_CERTIFICATE
    c = json.dumps(content)
    print(c)
    response = session.post(url, c)
    rc = response.status_code
    debug(rc)
    return rc

def debug(*args):
    if (True):
        print(*args)
        
    output = ' '.join(map(str, args))
    output = output + "\n"
    with open('log_file.txt', "a") as log_file:
        log_file.write(output)

def send_to_iot_platform(series, smartdata):
    print(f"Sending series: {series}")
    HOST = "iot.ufsc.br"
    create_url ='https://'+HOST+'/api/create.php'
    put_url = "https://"+HOST+"/api/put.php"
    get_url = "https://"+HOST+"/api/get.php"
    MY_CERTIFICATE = ('2066765E295F21E42842DE815291C91AB283C31C.pem', '2066765E295F21E42842DE815291C91AB283C31C.key')

    send_to_iot(create_url, series, MY_CERTIFICATE)

    for data in smartdata:
        send_to_iot(put_url, data, MY_CERTIFICATE)

# Example usage
csv_file_path = 'cleaned_vector_data.csv'
output_directory = 'output_smartdata'
generate_smartdata_in_batches(csv_file_path, output_directory)
