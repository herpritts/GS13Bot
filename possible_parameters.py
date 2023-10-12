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
    with open(filename, 'r', encoding="utf-8") as file:
        json_data = json.load(file)

    values = [value_entry[field] for value_entry in json_data["CodeList"][0]["ValidValue"]]

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
    if output_dir is None:
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))

    try:
        with open(json_file_path, 'r', encoding='UTF-8') as f:
            data = json.load(f)

        output_data = {}

        for key, item in data.items():
            if "PossibleValuesSource" in item and "PossibleValuesField" in item:
                source = os.path.join(output_dir, item["PossibleValuesSource"])
                field = item["PossibleValuesField"]

                with open(source, 'r', encoding='UTF-8') as source_f:
                    source_data = json.load(source_f)
                field_values = [x[field] for x in source_data['CodeList'][0]['ValidValue']]
                output_data[key] = field_values
            elif "PossibleValues" in item:
                output_data[key] = item["PossibleValues"]

        with open(os.path.join(output_dir, 'possible_values.json'), 'w', 
                  encoding='UTF-8') as output_f:
            json.dump(output_data, output_f, indent=4, sort_keys=True)

    except FileNotFoundError as err:
        print(f"The file '{err.filename}' could not be found. Please check the file path and try again.")
    except json.JSONDecodeError as err:
        print(f"An error occurred while decoding the JSON file: {err}")
    except Exception as err:
        print(f"An error occurred: {err}")


if __name__ == "__main__":
    extract_possible_values_to_json('./search_params.json')
    print("The possible values have been generated.")

