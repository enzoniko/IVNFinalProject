import sumolib

# Replace with your actual .net.xml file
net_file = '../artery/scenarios/monitorAV/LuSTNanoScenario/lust.net.xml'

# Create a SUMO network object
net = sumolib.net.readNet(net_file)

# Get the boundary of the SUMO network
net_bounds = net.getBBoxXY()

def sumo_to_omnetpp(x, y, net_bounds):
    """Converts SUMO coordinates to OMNeT++ coordinates.

    Args:
      x: X-coordinate in SUMO.
      y: Y-coordinate in SUMO.
      net_bounds: The bounding box of the SUMO network.

    Returns:
      A tuple (x, y) representing the OMNeT++ coordinates.
    """
    width = net_bounds[1][0] - net_bounds[0][0]
    height = net_bounds[1][1] - net_bounds[0][1]

    omnet_x = x - net_bounds[0][0]
    omnet_y = height - (y - net_bounds[0][1])  # Invert y-coordinate

    return omnet_x, omnet_y

def real_world_to_omnetpp(latlon_list, net, net_bounds):
    """Converts a list of real-world lat/lon coordinates to OMNeT++ coordinates.

    Args:
      latlon_list: A list of dictionaries, where each dictionary has 'lat' and 'lon' keys.
      net: The SUMO network object.
      net_bounds: The bounding box of the SUMO network.

    Returns:
      A string with the OMNeT++ coordinates in the desired format.
    """
    num_enodebs = len(latlon_list)
    j = 0
    output_str = ""
    for i, latlon in enumerate(latlon_list):
        x, y = net.convertLonLat2XY(latlon['Longitude'], latlon['Latitude'])
        omnet_x, omnet_y = sumo_to_omnetpp(x, y, net_bounds)

        # Filter out eNodeBs outside omnetpp bounds (must be within 0 and height and 0 and width)
        if omnet_x < 0 or omnet_x > net_bounds[1][0] - net_bounds[0][0] or omnet_y < 0 or omnet_y > net_bounds[1][1] - net_bounds[0][1]:
            num_enodebs -= 1
            continue

        output_str += f"*.eNodeB[{j}].mobility.initialX = {omnet_x}m\n"
        output_str += f"*.eNodeB[{j}].mobility.initialY = {omnet_y}m\n"
        j += 1

    print(f"Number of eNodeBs within bounds: {num_enodebs}")
    return output_str

def generate_bs_config(num_bs: int, bs_type: str, filename: str = "bs_config.txt") -> None:
    """
    Generates and writes BS configurations to a text file with a circular topology.

    Args:
        num_bs: The number of base stations to configure.
        bs_type: The type of base station ('gNodeB' or 'eNodeB').
        filename: The name of the output text file. Defaults to "bs_config.txt".
    """
    with open(filename, "w") as f:
        for i in range(num_bs):
            # Connection to the next BS in the circle
            next_bs = (i + 1) % num_bs
            f.write(f"*.{bs_type}[{i}].x2App[0].client.connectAddress = \"{bs_type}[{next_bs}]%x2ppp0\"\n")
            
            # Connection to the previous BS in the circle
            prev_bs = (i - 1 + num_bs) % num_bs
            f.write(f"*.{bs_type}[{i}].x2App[1].client.connectAddress = \"{bs_type}[{prev_bs}]%x2ppp0\"\n")

# Example usage
enodeb_latlon = [
    {'Latitude': 49.592169, 'Longitude': 6.117254},
    {'Latitude': 49.591035, 'Longitude': 6.125277},
    {'Latitude': 49.595352, 'Longitude': 6.126781},
    # Add more eNodeB lat/lon here...
]

omnetpp_ini_output = real_world_to_omnetpp(enodeb_latlon, net, net_bounds)
print(omnetpp_ini_output)

print("Generating BS config...")
generate_bs_config(3, "gNodeB", "gnodeb_config.txt")
