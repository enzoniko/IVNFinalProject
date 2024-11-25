from load_data import load_data
from eNodeBPosGenerator import real_world_to_omnetpp, net, net_bounds, generate_bs_config

# Load the data
data = load_data('270.csv')

# Get the OMNeT++ coordinates
omnetpp_ini_output = real_world_to_omnetpp(data, net, net_bounds)

# Write to a text file
with open('eNodeBPositions.txt', 'w') as f:
    f.write(omnetpp_ini_output)

generate_bs_config(74, 'gNodeB', 'bs_config.txt')