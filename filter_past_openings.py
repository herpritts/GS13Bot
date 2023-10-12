"""
This script filters job openings from a JSON file based on user-selected criteria.
"""

import json
import requests
import re
import html
from collections import defaultdict

def load_data_from_file(filename):
    """
    Load JSON data from a file.

    :param filename: The name of the file to load.
    :return: The loaded JSON data.
    """
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)

def select_filtering_criteria(data):
    """
    Interactively select filtering criteria based on the keys in the data.

    :param data: The data to select filtering criteria from.
    :return: A dictionary of filters.
    """
    sample_job = data['data'][0]
    keys = list(sample_job.keys())
    filters = {}

    while True:
        print("\nAvailable filtering criteria:")
        for idx, key in enumerate(keys, 1):
            filter_value = filters.get(key, None)
            filter_display = f" (Selected: {filter_value})" if filter_value else ""
            print(f"{idx}. {key}{filter_display}")

        choice = input("\nSelect a key number to filter by (or 'q' to finish): ")
        if choice == 'q':
            break
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(keys):
            print("Invalid choice. Try again.")
            continue

        key = keys[int(choice) - 1]
        values = [job[key] for job in data['data'] if job[key] is not None]

        first_value = values[0] if values else None

        if isinstance(first_value, list) and first_value and isinstance(first_value[0], dict):
            filters[key] = handle_list_of_dicts(values, filters, key)

        elif isinstance(first_value, dict):
            pass

        else:
            filters[key] = handle_other_values(values, filters, key)

        current_filtered_jobs = filter_jobs(data, filters)
        print(f"Results matching current filters: {len(current_filtered_jobs)}")

    return filters

def handle_list_of_dicts(values, filters, key):
    """
    Handle the case where the first value is a list of dictionaries.

    :param values: The values for the selected key.
    :param filters: The current filters.
    :param key: The selected key.
    :return: The updated filter for the selected key.
    """
    dict_keys = list(values[0][0].keys())
    for idx, dict_key in enumerate(dict_keys, 1):
        print(f"{idx}. {dict_key}")

    dict_key_choice = input("Select a key from the dictionary by entering its number: ")

    if not dict_key_choice.isdigit() or int(dict_key_choice) < 1 or int(dict_key_choice) > len(dict_keys):
        print("Invalid choice. Try again.")
        return filters[key]

    chosen_dict_key = dict_keys[int(dict_key_choice) - 1]

    unique_dict_values = sorted(list(set(d[chosen_dict_key] for sublist in values for d in sublist if d.get(chosen_dict_key))), key=str)
    for idx, val in enumerate(unique_dict_values, 1):
        print(f"{idx}. {val}")

    value_choice = input("Select a value by entering its number or type a keyword: ")

    if value_choice.isdigit() and 1 <= int(value_choice) <= len(unique_dict_values):
        value = unique_dict_values[int(value_choice) - 1]
        return {chosen_dict_key: value}
    else:
        keyword = value_choice.lower()
        value = lambda field: any(d.get(chosen_dict_key) and keyword in str(d[chosen_dict_key]).lower() for d in field)
        return value

def handle_other_values(values, filters, key):
    """
    Handle the case where the first value is not a list of dictionaries or a dictionary.

    :param values: The values for the selected key.
    :param filters: The current filters.
    :param key: The selected key.
    :return: The updated filter for the selected key.
    """
    unique_values = sorted(list(set(values)), key=str)
    for idx, val in enumerate(unique_values, 1):
        print(f"{idx}. {val}")
    value_choice = input(f"Select a value by entering its number or type a keyword: ")
    
    if value_choice.isdigit() and 1 <= int(value_choice) <= len(unique_values):
        value = unique_values[int(value_choice) - 1]
    else:
        keyword = value_choice.lower()
        value = lambda field: keyword in str(field).lower()
    return value

def filter_jobs(data, filters):
    """
    Filter jobs based on the provided filters.

    :param data: The data to filter.
    :param filters: The filters to apply.
    :return: The filtered data.
    """
    filtered_jobs = data['data']
    for key, value in filters.items():
        if key in filtered_jobs[0]:
            if callable(value):
                filtered_jobs = [job for job in filtered_jobs if value(job[key])]
            elif isinstance(value, dict) and isinstance(filtered_jobs[0][key], list):
                dict_key, dict_value = list(value.items())[0]
                filtered_jobs = [job for job in filtered_jobs if any(subdict.get(dict_key) == dict_value for subdict in job[key])]
            else:
                filtered_jobs = [job for job in filtered_jobs if str(job[key]) == str(value)]
        else:
            return []
    return filtered_jobs

def strip_html_tags(text):
    """Remove html tags from a string"""
    text = html.unescape(text)  # Unescape HTML entities
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def display_results(filtered_jobs, total_jobs):
    """
    Display the results of the filtering.

    :param filtered_jobs: The filtered jobs.
    :param total_jobs: The total number of jobs.
    """
    if len(filtered_jobs) == 0:
        print("No jobs found.")
    else:
        print(f"\nNumber of filtered results: {len(filtered_jobs)}")
        print(f"Total number of job listings: {total_jobs}\n")

        for idx, job in enumerate(filtered_jobs, 1):
            title = job.get('positionTitle', 'N/A')
            city = job['positionLocations'][0].get('positionLocationCity', 'N/A') if job.get('positionLocations') else 'N/A'
            state = job['positionLocations'][0].get('positionLocationState', 'N/A') if job.get('positionLocations') else 'N/A'
            posted_date = job.get('positionOpenDate', 'N/A')
            if posted_date != 'N/A':
                posted_date = posted_date.split('T')[0]  # Get the date part only, without the time
            print(f"{idx}. Job Title: {title}, City: {city}, State: {state}, Posted Date: {posted_date}")

        while True:
            choice = input("\nSelect a job number for more information, 'save' to save the data, or 'q' to quit: ")
            if choice.lower() == 'q':
                break
            elif choice.lower() == 'save':
                # Fetch additional data for each job and add it to the job data
                for job in filtered_jobs:
                    href = job['_links'][0].get('href', '')
                    if href:
                        url = f"https://data.usajobs.gov{href}"
                        response = requests.get(url)
                        if response.status_code == 200:
                            additional_data = response.json()
                            # Strip HTML tags and replace \n with line breaks in the additional data
                            for key, value in additional_data.items():
                                if isinstance(value, str):
                                    value = strip_html_tags(value)
                                    additional_data[key] = value.replace('\\n', '\n')
                            job.update(additional_data)

                with open('filtered_jobs.json', 'w') as f:
                    json.dump(filtered_jobs, f, indent=4)
                print("Data saved to filtered_jobs.json")
                continue

            if not choice.isdigit() or int(choice) < 1 or int(choice) > len(filtered_jobs):
                print("Invalid choice. Try again.")
                continue

            job = filtered_jobs[int(choice) - 1]
            print("\nSelected Job Details:")
            for key, value in job.items():
                print(f"{key}: {value}")

            # Fetch additional data from the URL in the href field
            href = job['_links'][0].get('href', '')
            if href:
                url = f"https://data.usajobs.gov{href}"
                response = requests.get(url)
                if response.status_code == 200:
                    additional_data = response.json()
                    print("\nAdditional Job Details:")
                    for key, value in additional_data.items():
                        if isinstance(value, str):
                            value = strip_html_tags(value)
                            value = value.replace('\\n', '\n')
                        print(f"{key}: {value}")

def generate_unique_values():
    # Read the JSON file
    with open('filtered_jobs.json', 'r') as f:
        jobs = json.load(f)

    # Initialize a dictionary to store the unique values and their counts
    unique_values = defaultdict(lambda: defaultdict(int))

    # Iterate over the jobs and their keys
    for job in jobs:
        for key, value in job.items():
            # If the value is a list, iterate over its elements
            if isinstance(value, list):
                for element in value:
                    unique_values[key][str(element)] += 1
            else:
                unique_values[key][str(value)] += 1

    # Convert the defaultdicts to regular dicts for JSON serialization
    unique_values = {key: dict(values) for key, values in unique_values.items()}

    # Save the unique values and their counts to a new JSON file
    with open('unique_values.json', 'w') as f:
        json.dump(unique_values, f, indent=4)

def main():
    """
    Main entry point of the program.
    """
    print("Welcome to the USA Jobs Filtering Tool!")
    filename = input("\nPlease enter the path to your JSON file: ")

    try:
        data = load_data_from_file(filename)
        print("\nHere are the available filtering criteria:")
        filters = select_filtering_criteria(data)
        filtered_jobs = filter_jobs(data, filters)
        display_results(filtered_jobs, len(data['data']))
        generate_unique_values()
    except FileNotFoundError as error:
        print(f"File not found: {error.filename}")
    except KeyError as error:
        print(f"Invalid JSON file: {error}")
    except Exception as error:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    main()
    