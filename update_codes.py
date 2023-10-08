"""
This module fetches data from the USAJobs API, saves it to local JSON files, and uses 
environment variables to authenticate the API requests.

Functions:
    fetch_environment_variables() -> Dict[str, str]:
        Fetch sensitive data from environment variables.
    fetch_api_data(base_url: str, endpoint: str, headers: Dict[str, str]) -> Optional[Dict]:
        Fetch data from a given API endpoint.
    save_to_json(data: Dict, filename: str) -> None:
        Save data to a JSON file.
    fetch_and_save_data(base_url: str, endpoints: Dict[str, str], headers: Dict[str, str]) -> None:
        Fetch and save data for multiple endpoints.
"""

import sys
import json
import logging
from typing import Dict, Optional
import requests
from utils import fetch_environment_variables, save_to_json

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_api_data(base_url: str, endpoint: str, headers: Dict[str, str]) -> Optional[Dict]:
    """Fetch data from a given API endpoint."""
    try:
        response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        logging.error("Error fetching data from %s: %s", endpoint, err)
        return None

def fetch_and_save_data(base_url: str, endpoints: Dict[str, str], headers: Dict[str, str], prefix: str) -> None:
    """Fetch and save data for multiple endpoints."""
    for name, endpoint in endpoints.items():
        data = fetch_api_data(base_url, endpoint, headers)
        if data:
            filename = f"{prefix}_{name.lower().replace(' ', '_')}.json"
            save_to_json(data, filename)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    BASE_URL = "https://data.usajobs.gov/api"
    ENDPOINTS_FILE = "endpoints.json"
    PREFIX = "codes"

    try:
        headers = fetch_environment_variables()
    except ValueError as e:
        logging.error("Error fetching environment variables: %s", e)
        sys.exit(1)

    with open(ENDPOINTS_FILE, "r", encoding="utf-8") as f:
        endpoints = json.load(f)

    fetch_and_save_data(BASE_URL, endpoints, headers, PREFIX)
