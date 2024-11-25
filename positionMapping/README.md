To run these scripts you need to install the sumolib library.
You can install it by running the following command:
```bash
pip install sumolib
```

After installing the sumolib you need to correctly set the path to the net file of the SUMO scenario in the BaseStationPosGenerator.py script.
You can do this by changing the value of the variable `net_file` in the script.

Lastly you need to have csv files from openCellId with the cell towers data, and use them within the getPositions.py script, setting the number of Base stations correctly.