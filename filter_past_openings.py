import json

def load_data_from_file(filename):
    with open(filename, 'r') as file:
        return json.load(file)

def select_filtering_criteria(data):
    # Display available keys for filtering
    sample_job = data['data'][0]
    keys = list(sample_job.keys())
    
    # Keep track of selected filters
    filters = {}

    while True:
        # Display available keys and selected filters
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

        # Check if the values are lists
        first_value = values[0] if values else None

        if isinstance(first_value, list) and first_value and isinstance(first_value[0], dict):
            # Handle list values which are dictionaries
            dict_keys = list(first_value[0].keys())
            for idx, dict_key in enumerate(dict_keys, 1):
                print(f"{idx}. {dict_key}")

            dict_key_choice = input(f"Select a key from the dictionary by entering its number: ")

            if not dict_key_choice.isdigit() or int(dict_key_choice) < 1 or int(dict_key_choice) > len(dict_keys):
                print("Invalid choice. Try again.")
                continue

            chosen_dict_key = dict_keys[int(dict_key_choice) - 1]
            
            # Gather unique values for the chosen dictionary key across all dictionaries within the lists
            unique_dict_values = sorted(list(set(d[chosen_dict_key] for sublist in values for d in sublist if d.get(chosen_dict_key))), key=str)
            for idx, val in enumerate(unique_dict_values, 1):
                print(f"{idx}. {val}")

            value_choice = input(f"Select a value by entering its number or type a keyword: ")

            # Check if the user entered a number or a keyword
            if value_choice.isdigit() and 1 <= int(value_choice) <= len(unique_dict_values):
                value = unique_dict_values[int(value_choice) - 1]
                filters[key] = {chosen_dict_key: value}  # Store as a nested dictionary for filtering
            else:
                # User input is treated as a keyword
                keyword = value_choice.lower()  # Convert keyword to lowercase
                value = lambda field: any(d.get(chosen_dict_key) and keyword in str(d[chosen_dict_key]).lower() for d in field)
                filters[key] = value

            # Display the number of results matching current filters
            current_filtered_jobs = filter_jobs(data, filters)
            print(f"Results matching current filters: {len(current_filtered_jobs)}")
            continue
    
        elif isinstance(first_value, dict):
            # TODO: Additional handling for direct dictionary values if needed
            pass

        else:
            # Handle basic hashable types (e.g., strings, numbers)
            unique_values = sorted(list(set(values)), key=str)
            for idx, val in enumerate(unique_values, 1):
                print(f"{idx}. {val}")
            value_choice = input(f"Select a value by entering its number or type a keyword: ")
            
            # Check if the user entered a number or a keyword
            if value_choice.isdigit() and 1 <= int(value_choice) <= len(unique_values):
                value = unique_values[int(value_choice) - 1]
            else:
                # User input is treated as a keyword
                keyword = value_choice.lower()  # Convert keyword to lowercase
                value = lambda field: keyword in str(field).lower()
            filters[key] = value

            # Display the number of results matching current filters
            current_filtered_jobs = filter_jobs(data, filters)
            print(f"Results matching current filters: {len(current_filtered_jobs)}")
    
    return filters



def filter_jobs(data, filters):
    filtered_jobs = data['data']
    for key, value in filters.items():
        if key in filtered_jobs[0]:  # Check if the key exists
            # Check if the filter value is a lambda function (for keyword checks)
            if callable(value):
                filtered_jobs = [job for job in filtered_jobs if value(job[key])]
            elif isinstance(value, dict) and isinstance(filtered_jobs[0][key], list):  # Check for nested dictionary within list structure
                dict_key, dict_value = list(value.items())[0]
                filtered_jobs = [job for job in filtered_jobs if any(subdict.get(dict_key) == dict_value for subdict in job[key])]
            else:
                filtered_jobs = [job for job in filtered_jobs if str(job[key]) == str(value)]
    return filtered_jobs



def display_results(filtered_jobs, total_jobs):
    print(f"\nNumber of filtered results: {len(filtered_jobs)}")
    print(f"Total number of job listings: {total_jobs}\n")

def main():
    print("Welcome to the USA Jobs Filtering Tool!")
    filename = input("\nPlease enter the path to your JSON file: ")
    
    try:
        data = load_data_from_file(filename)
        print("\nHere are the available filtering criteria:")
        filters = select_filtering_criteria(data)
        filtered_jobs = filter_jobs(data, filters)
        display_results(filtered_jobs, len(data['data']))
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
