"""
This module contains functions for extracting possible parameter values from JSON files.

Functions:
    get_field_values_from_json_file(filename, field):
        Extracts the list of values from a specified field in a given JSON file.
    extract_possible_values_to_json(json_file_path, output_dir=None):
        Extracts the possible values from a JSON file and writes them to another JSON file.
"""

import json
import os

def get_field_values_from_json_file(filename, field):
    """
    Extracts the list of values from a specified field in a given JSON file.

    Parameters:
        filename (str): The name of the JSON file.
        field (str): The field from which values need to be extracted.

    Returns:
        list: List of values from the specified field.
    """
    # Open the JSON file and load the data into a dictionary
    with open(filename, 'r', encoding="utf-8") as file:
        json_data = json.load(file)

    # Extract the values from the specified field and add them to a list
    values = []
    for value_entry in json_data["CodeList"][0]["ValidValue"]:
        values.append(value_entry[field])

    # Return the list of values
    return values


def extract_possible_values_to_json(json_file_path, output_dir=None):
    """
    Extracts the possible values from a JSON file and writes them to another JSON file.

    Parameters:
        json_file_path (str): The path of the JSON file to read.
        output_dir (str): The directory where the output JSON files will be saved.

    Returns:
        None
    """
    # Set the default output directory to a subdirectory called 'data'
    if output_dir is None:
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))

    try:
        # Open the input JSON file and load the data into a dictionary
        with open(json_file_path, 'r', encoding='UTF-8') as f:
            data = json.load(f)

        # Create an empty dictionary to store the output data
        output_data = {}

        # Loop through each key-value pair in the input dictionary
        for key, item in data.items():
            # If the item has 'PossibleValuesSource' and 'PossibleValuesField' keys,
            # extract the possible values
            if "PossibleValuesSource" in item and "PossibleValuesField" in item:
                # Get the source file path and field name from the input dictionary
                source = os.path.join(output_dir, item["PossibleValuesSource"])
                field = item["PossibleValuesField"]

                # Extract the possible values from the source file and
                # add them to the output dictionary
                with open(source, 'r', encoding='UTF-8') as source_f:
                    source_data = json.load(source_f)
                field_values = [x[field] for x in source_data['CodeList'][0]['ValidValue']]
                output_data[key] = field_values
            # If the item has a 'PossibleValues' key, add the possible values
            # directly to the output dictionary
            elif "PossibleValues" in item:
                output_data[key] = item["PossibleValues"]

        # Write the output dictionary to a JSON file in the specified output directory
        with open(os.path.join(output_dir, 'possible_values.json'), 'w', 
                  encoding='UTF-8') as output_f:
            json.dump(output_data, output_f, indent=4, sort_keys=True)

    # Catch any exceptions that occur during the function and print an error message
    except FileNotFoundError as err:
        print(f"The file '{err.filename}' could not be found. Please check the file path and try again.")
    except json.JSONDecodeError as err:
        print(f"An error occurred while decoding the JSON file: {err}")
    except Exception as err:
        print(f"An error occurred: {err}")


# Run the function and display the results
extract_possible_values_to_json('./search_params.json')
print("The possible values have been generated.")
