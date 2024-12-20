import pandas as pd
import numpy as np
import sys

def load_csv(file_path):
    """Loads a CSV file into a pandas DataFrame.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        pandas.DataFrame: The loaded DataFrame.
    """

    return pd.read_csv(file_path)

def filter_by_type(data, data_type):
    """Filters data based on the specified data type.

    Args:
        data (pandas.DataFrame): The input DataFrame.
        data_type (str): The desired data type ('scalar', 'attr', or 'vector').

    Returns:
        pandas.DataFrame: The filtered DataFrame.
    """

    return data[data['type'] == data_type]

def clean_scalar_data(scalar_data):
    """Cleans scalar data by dropping NaN values and selecting relevant columns.

    Args:
        scalar_data (pandas.DataFrame): The scalar data DataFrame.

    Returns:
        pandas.DataFrame: The cleaned scalar data DataFrame.
    """

    scalar_data = scalar_data.dropna(subset=['value'])
    scalar_data_filtered = scalar_data[['module', 'name', 'value']]
    return scalar_data_filtered

def clean_attr_data(attr_data):
    """Cleans attribute data by filtering for 'unit' and dropping NaN values.

    Args:
        attr_data (pandas.DataFrame): The attribute data DataFrame.

    Returns:
        pandas.DataFrame: The cleaned attribute data DataFrame.
    """

    attr_units = attr_data[attr_data["attrname"] == "unit"]
    attr_units = attr_units.dropna(subset=["attrvalue"])
    attr_units_filtered = attr_units[["module", "name", "attrvalue"]]
    return attr_units_filtered

def clean_vector_data(vector_data):
    """Cleans vector data by dropping NaN values and selecting relevant columns.

    Args:
        vector_data (pandas.DataFrame): The vector data DataFrame.

    Returns:
        pandas.DataFrame: The cleaned vector data DataFrame.
    """

    vector_data = vector_data.dropna(subset=['vectime', 'vecvalue'])

    # Drop rows where the module has 'sctp' in it
    vector_data = vector_data[~vector_data['module'].str.contains('sctp')]

    # Check what unique values in the "name" column have all the rows with the 'vecvalue' (vecvalue column contain a vector of values) values constant
    unique_names = vector_data["name"].unique()
    for name in unique_names:

        # Get all the rows with the same name
        name_rows = vector_data[vector_data["name"] == name]

        # Get the standard deviation of the vecvalue column
        for index, row in name_rows.iterrows():
            #vecvalue = row["vecvalue"]
            vectime = row["vectime"]

            # Transform the string into a list of floats
            #vecvalue = np.array([float(x) for x in vecvalue.split(" ")])
            vectime = np.array([float(x) for x in vectime.split(" ")])

            #vecvalue_std = vecvalue.std()
            vectime_std = vectime.std()

            # If the standard deviation is zero, then all the values in the vecvalue column are the same
            if vectime_std == 0:
                print(f"Name: {name}, Mean: {vectime.mean()}, Std: {vectime_std}")

                # Drop all the rows with the same name
                vector_data = vector_data[vector_data["name"] != name]

            """ if vecvalue_std == 0:
                print(f"Name: {name}, Mean: {vecvalue.mean()}, Std: {vecvalue_std}")

                # Drop all the rows with the same name
                vector_data = vector_data[vector_data["name"] != name] """
    

    vector_data_filtered =  vector_data[['module', 'name', 'vectime', 'vecvalue']] # vector_data[['module', 'name']] #
    return vector_data_filtered

def merge_data(scalar_data, attr_data):
    """Merges scalar data with attribute data to add units.

    Args:
        scalar_data (pandas.DataFrame): The scalar data DataFrame.
        attr_data (pandas.DataFrame): The attribute data DataFrame.

    Returns:
        pandas.DataFrame: The merged DataFrame.
    """

    scalar_data_with_units = pd.merge(scalar_data, attr_data, on=['module', 'name'], how='left')
    return scalar_data_with_units

def main():
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.max_columns', None)
    pd.set_option("expand_frame_repr", False) # print cols side by side as it's supposed to be
    pd.set_option('display.max_rows', None)

    # Example file path (update with the correct path)
    file_path = "vectors.csv"
    
    # Load CSV
    data = load_csv(file_path)
    print(f"Loaded data with {len(data)} rows.")

    print("\nData Columns:")
    print("----------------------------------------")
    print(data.columns)
    print("----------------------------------------")
    
    # Filter data by type
    #scalar_data = filter_by_type(data, 'scalar')
    attr_data = filter_by_type(data, 'attr')
    vector_data = filter_by_type(data, 'vector')

    #print(f"Filtered scalar data with {len(scalar_data)} rows.")
    print(f"Filtered attribute data with {len(attr_data)} rows.")
    print(f"Filtered vector data with {len(vector_data)} rows.")
    
    # Clean data
    #cleaned_scalar_data = clean_scalar_data(scalar_data)
    cleaned_attr_data = clean_attr_data(attr_data)
    cleaned_vector_data = clean_vector_data(vector_data)

    # Get a list of the unique "module" values
    unique_modules = cleaned_vector_data["module"].unique()
    print(f"\nUnique 'module' values: ")
    print("----------------------------------------")
   
    print(list(unique_modules))
    print("----------------------------------------")

    # Save the vector data to a CSV file
    #cleaned_vector_data.to_csv("cleaned_vector_data.csv", index=False)
    
    # Save only 3 rows of the vector data to a CSV file
    cleaned_vector_data.head(3).to_csv("cleaned_vector_data_head.csv", index=False)

    # Get all the unique "name" values
    unique_names = cleaned_vector_data["name"].unique()
    print(f"\nUnique 'name' values (variable names): ")
    print("----------------------------------------")
    for name in unique_names:
        print(name)
    print("----------------------------------------")

    """ unique_names = cleaned_scalar_data["name"].unique()
    print(f"\nUnique 'name' values (variable names): ")
    print("----------------------------------------")
    for name in unique_names:
        print(name) 
    print("----------------------------------------") """
    

    """ # Merge scalar data with units
    scalar_data_with_units = merge_data(cleaned_scalar_data, cleaned_attr_data)

    # Show scalar data with and without missing units
    print("\nScalar Data with Missing Units:")
    print("----------------------------------------")
    print(scalar_data_with_units[scalar_data_with_units['attrvalue'].isnull()])
    print("----------------------------------------")

    print("\nScalar Data without Missing Units:")
    print("----------------------------------------")
    print(scalar_data_with_units[~scalar_data_with_units['attrvalue'].isnull()])
    print("----------------------------------------") """

    # Merge vector data with units
    vector_data_with_units = merge_data(cleaned_vector_data, cleaned_attr_data)


    # Show vector data with and without missing units
    print("\nVector Data with Missing Units:")
    print("----------------------------------------")
    #print(vector_data_with_units[vector_data_with_units['attrvalue'].isnull()])
    vector_data_with_missing_units = vector_data_with_units[vector_data_with_units['attrvalue'].isnull()]

    # Get all the unique "name" values
    unique_names = vector_data_with_missing_units["name"].unique()
    print(f"\nUnique 'name' values (variable names) with missing units: ")
    
    for name in unique_names:
        print(name)


    print("----------------------------------------")

    print("\nVector Data without Missing Units:")
    print("----------------------------------------")
    #print(vector_data_with_units[~vector_data_with_units['attrvalue'].isnull()])

    vector_data_without_missing_units = vector_data_with_units[~vector_data_with_units['attrvalue'].isnull()]

    # Get all the unique "name" values
    unique_names = vector_data_without_missing_units["name"].unique()

    # Get the attrvalue for each unique name
    for name in unique_names:
        attrvalue = vector_data_without_missing_units[vector_data_without_missing_units["name"] == name]["attrvalue"].iloc[0]
        print(f"{name}: {attrvalue}")
        

    print("----------------------------------------")

    # Get all the unique "attrvalue" values
    unique_attr_values = cleaned_attr_data["attrvalue"].unique()
    print(f"\nUnique 'attrvalue' values (units): {unique_attr_values}")

    

if __name__ == "__main__":

    orig_stdout = sys.stdout
    f = open('vectorsReport.txt', 'w')
    sys.stdout = f

    main()

    sys.stdout = orig_stdout
    f.close()