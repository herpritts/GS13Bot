"""
This module provides an extended Python function to perform a job search using the USAJobs.gov API. 
The function allows for more search parameters than the standard API search, including keyword, 
position title, salary range, job category, location, and more.

The module also imports the `fetch_environment_variables()` function from the `update_codes.py` 
file to fetch sensitive data from environment variables, including the authorization key, 
user agent, and host.

Example usage:
    # Perform a job search for software engineer positions in Washington, DC
    results = job_search(keyword='software engineer', location_name='Washington, DC')

    # Print the search results
    print(results)
"""

import json
import logging
from pathlib import Path
from typing import Dict
import os
from dotenv import load_dotenv
import requests
import requests.exceptions

def fetch_headers():
    """
    Fetch the header information needed to authenticate the API request and identify the user agent.

    Returns:
        dict: Dictionary containing the header information
    """
    load_dotenv()
    headers = {
        'Authorization-Key': os.environ.get('USAJOBS_AUTHORIZATION_KEY'),
        'User-Agent': os.environ.get('USAJOBS_USER_AGENT')
    }
    if None in headers.values():
        raise Exception("Missing required environment variables")
    return headers

def prepare_params(**kwargs):
    """
    Prepare the query parameters for the API request based on provided keyword arguments.
    
    Parameters:
        **kwargs: Arbitrary keyword arguments

    Returns:
        dict: Dictionary containing query parameters
    """
    ...
    params = {}
    for key, value in kwargs.items():
        if value is not None:
            params[key] = value
    return params

def make_api_call(BASE_URL, HEADERS, params):
    """
    Make an API call to the USAJobs.gov API and return the response.

    Parameters:
        BASE_URL (str): The base URL for the API
        HEADERS (dict): The headers for the API request
        params (dict): The query parameters for the API request

    Returns:
        dict: Dictionary containing the API response or an error message
    """
    ...
    try:
        response = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return {'error': f'API call failed with status code {response.status_code}'}
    except requests.exceptions.Timeout:
        return {'error': 'API call timed out'}
    except requests.exceptions.RequestException as err:
        return {'error': f'API call failed with exception: {err}'}

# Define constants for the API endpoint and other fixed values
BASE_URL = 'https://data.usajobs.gov/api/Search'
KEYWORD = 'Health Physicist'
LOCATIONNAME = 'Portsmouth, Virginia'
RESULTS_PER_PAGE = 50
PAY_GRADE_LOW = 13
RADIUS = 25
ANNOUNCEMENT_CLOSING_TYPE_FILTER = '03'

def job_search(**kwargs):
    """
    Perform a job search using the USAJobs.gov API based on given keyword arguments.

    Parameters:
        **kwargs: Arbitrary keyword arguments

    Returns:
        dict: Dictionary containing the API response
    """
    ...
    HEADERS = fetch_headers()
    params = prepare_params(**kwargs)
    try:
        response = make_api_call(BASE_URL, HEADERS, params)
    except requests.exceptions.RequestException as err:
        raise Exception(f"Error making API call: {err}")
    if 'error' in response:
        raise Exception(response['error'])
    return response

# Load the sample search results JSON file to understand the data structure
with open("./data/data_search_results.json", "r", encoding="UTF-8") as f:
    search_results = json.load(f)

# Count the number of items in "PositionLocation" for each item
def count_position_locations(search_results):
    """
    Counts the number of PositionLocation entries in each SearchResultItem in a given search result.

    Parameters:
        search_results (dict): The search result dictionary to process.

    Returns:
        None
    """
    ...
    # Create a logger object
    logger = logging.getLogger(__name__)

    if 'SearchResult' in search_results and 'SearchResultItems' in search_results['SearchResult']:
        # Loop through each SearchResultItem in the search result
        for i, item in enumerate(search_results['SearchResult']['SearchResultItems']):
            # Get the list of PositionLocation entries for the current SearchResultItem
            position_title = item.get('MatchedObjectDescriptor', {}).get('PositionTitle', 'Unknown Title')
            position_locations = item.get('MatchedObjectDescriptor', {}).get('PositionLocation', [])
            if not isinstance(position_locations, list):
                position_locations = [position_locations]
            announcement_closing_type = item["MatchedObjectDescriptor"]["UserArea"]["Details"]["AnnouncementClosingType"]
            # Log the number of PositionLocation entries for the current SearchResultItem
            logger.info("Item %s: PositionTitle: %s, Number of Locations: %s, AnnouncementClosingType: %s", i+1, position_title, len(position_locations), announcement_closing_type)

def filter_search_results(search_results):
    """
    Filters the search results to remove items where the AnnouncementClosingType is "03".

    Parameters:
        search_results (dict): The search result dictionary to process.

    Returns:
        dict: The filtered search result dictionary.
    """
    ...
    if 'SearchResult' in search_results and 'SearchResultItems' in search_results['SearchResult']:
        # Create a new list with items that don't match the condition
        filtered_items = [item for item in search_results['SearchResult']['SearchResultItems'] if item.get("MatchedObjectDescriptor", {}).get("UserArea", {}).get("Details", {}).get("AnnouncementClosingType") == ANNOUNCEMENT_CLOSING_TYPE_FILTER]
        num_filtered_items = len(filtered_items)

        # Create a new dictionary with the filtered list
        filtered_search_results = {'SearchResult': {'SearchResultItems': filtered_items}}

        return filtered_search_results, num_filtered_items
    else:
        raise ValueError("Invalid search results format")

def save_to_json(data: Dict, filename: str) -> None:
    """Save data to a JSON file."""
    path = Path("data") / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    logging.info("Data saved to %s", path)

def check_for_job_posting():
    """
    Checks if there are any job postings for Health Physicist positions in Portsmouth, VA.

    Returns:
        bool: True if there are job postings, False if there are no job postings, None if there was an error
    """
    ...
    try:
        # Perform a job search for Health Physicist positions in Portsmouth, VA
        results = job_search(Keyword='Health Physicist', LocationName='Portsmouth, Virginia', Radius=RADIUS, PayGradeLow=PAY_GRADE_LOW, ResultsPerPage=RESULTS_PER_PAGE)
        filtered_results, num_filtered_results = filter_search_results(results)

        # Call the function to display the results
        count_position_locations(results)

        # Save the search results to a JSON file
        save_to_json(results, 'search_results.json')
        save_to_json(filtered_results, 'filtered_search_results.json')

        if num_filtered_results > 0:
            return True
    except Exception as err:
        print(f"Error: {err}")
        return None

# Example usage:
if __name__ == "__main__":
    check_for_job_posting()
