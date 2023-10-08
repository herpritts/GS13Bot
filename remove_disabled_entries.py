"""
This module provides functions for removing disabled entries from JSON data.

The `remove_disabled_entries()` function takes a JSON data object as input and 
removes all the disabled entries from the "ValidValue" field in the "CodeList" object. 
The function returns a new JSON data object with the disabled entries removed.

The `remove_disabled_entries_from_json_files_in_folder()` function takes a folder path 
as input and iterates through every JSON file in the folder. For each file, the function 
reads the JSON data, removes the disabled entries using the `remove_disabled_entries()` 
function, and writes the updated JSON data back to the file.

Example usage:

    # Remove disabled entries from a single JSON file
    with open('data.json', 'r', encoding='utf-8') as file:
        json_data = json.load(file)
    updated_json = remove_disabled_entries(json_data)

    # Remove disabled entries from all JSON files in a folder
    remove_disabled_entries_from_json_files_in_folder('./data')
"""

import os
import json

def remove_disabled_entries(json_data):
    """
    Remove all the disabled entries from the given JSON data.
    
    Parameters:
        json_data (dict): The JSON data containing "CodeList" and "ValidValue" fields.
    
    Returns:
        dict: A new JSON data with disabled entries removed.
    """
    enabled_values = []
    for entry in json_data.get("CodeList", [{}])[0].get("ValidValue", []):
        if entry.get("IsDisabled", "No") != "Yes":
            enabled_values.append(entry)
    json_data["CodeList"][0]["ValidValue"] = enabled_values
    return json_data

def remove_disabled_entries_from_json_files_in_folder(folder_path):
    """
    Iterate through every JSON file in a given folder and remove disabled entries.
    
    Parameters:
        folder_path (str): The path to the folder containing JSON files.
    
    Returns:
        None: The function modifies the JSON files in place.
    """
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, 'r', encoding="utf-8") as file:
                    json_data = json.load(file)
                updated_json = remove_disabled_entries(json_data)
                with open(file_path, 'w', encoding="utf-8") as file:
                    json.dump(updated_json, file, indent=4)
                print(f"Processed {filename}")
            except (FileNotFoundError, json.JSONDecodeError) as err:
                print(f"Error processing {filename}: {err}")

def main():
    """
    Remove disabled entries from all JSON files in a folder.
    """
    folder_path = "./data"
    remove_disabled_entries_from_json_files_in_folder(folder_path)

if __name__ == '__main__':
    main()
