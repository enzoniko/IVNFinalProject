import pandas as pd

def load_data(filename):

    data = pd.read_csv('270.csv')



    """
    0 |Radio|	The generation of broadband cellular network technology (Eg. LTE, GSM)
    1 |MCC|	Mobile country code. This info is publicly shared by International Telecommunication Union (link)
    2 |MNC|	Mobile network code. This info is publicly shared by International Telecommunication Union (link)
    3 |LAC/TAC/NID|	Location Area Code
    4 |CID|	This is a unique number used to identify each Base transceiver station or sector of BTS
    7 |Range|	Approximate area within which the cell could be. (In meters)
    5 |Longitude|	Longitude, is a geographic coordinate that specifies the east-west position of a point on the Earth's surface
    6 |Latitude|	Latitude is a geographic coordinate that specifies the north–south position of a point on the Earth's surface.
    8 |Samples|	Number of measures processed to get a particular data point
    9 |Changeable=1|	The location is determined by processing samples
    10 |Changeable=0|	The location is directly obtained from the telecom firm
    11 |Created|	When a particular cell was first added to database (UNIX timestamp)
    12 |Updated|	When a particular cell was last seen (UNIX timestamp)
    13 |AverageSignal|	To get the positions of cells, OpenCelliD processes measurements from data contributors. Each measurement includes GPS location of device + Scanned cell identifier (MCC-MNC-LAC-CID) + Other device properties (Signal strength). In this process, signal strength of the device is averaged. Most ‘averageSignal’ values are 0 because OpenCelliD simply didn’t receive signal strength values.

    """

    print(f"Number of columns: {len(data.columns)}")

    # Set the name of the columns
    data.columns = ['Radio', 'MCC', 'MNC', 'LAC', 'CID', 'Range', 'Longitude', 'Latitude', 'Samples', 'Changeable1', 'Changeable0', 'Created', 'Updated', 'AverageSignal']

    # Select Radio == LTE
    data = data[data['Radio'] == 'LTE']
    print(data.describe())
    # Select Longitude between 6.030969 and 6.216758
    # Select Latitude  between 49.549099 and 49.652578
    data = data[(data['Longitude'] >= 6.030969) & (data['Longitude'] <= 6.216758) & (data['Latitude'] >= 49.549099) & (data['Latitude'] <= 49.652578)]

    print(f"Number of repeated CIDs: {data.duplicated(subset='CID').sum()}")
    
    # Drop duplicates (same CID)
    data = data.drop_duplicates(subset='CID', keep='first')

    
    # Check if there are repeated CIDs
    print(f"Number of repeated CIDs: {data.duplicated(subset='CID').sum()}")
    print(f"Number of rows: {len(data)}")

    print(data.describe())

    # Get a list with dicts {lat: x, lon: y}
    data = data[['Latitude', 'Longitude']].to_dict(orient='records')

    print(data[:5])

    return data

if __name__ == '__main__':
    load_data('270.csv')