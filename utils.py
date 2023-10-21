"""
utils.py

This module contains utility functions for logging, environment variable fetching, 
and JSON file handling.

Functions:
    init_logging() -> logging.Logger:
        Initializes the logging module for Azure App Service compatibility.

    fetch_environment_variables() -> Dict[str, str]:
        Fetches sensitive data from environment variables.

    save_to_json(data_dict: dict, filename: str) -> None:
        Saves the given dictionary to a JSON file.

    load_from_json(filename: str) -> dict:
        Loads a dictionary from a JSON file.

This module is part of a larger project that interacts with the USAJobs API and a Telegram bot. 
It uses environment variables for sensitive data like authorization keys and user agents. 
The JSON file handling functions are used to persist data between sessions.

"""

import logging
import os
import sys
from typing import Dict
from pathlib import Path
import json
from dotenv import load_dotenv

def init_logging() -> logging.Logger:
    """
    Initializes the logging module for Azure App Service compatibility.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logger = logging.getLogger(__name__)
    return logger

def fetch_environment_variables() -> Dict[str, str]:
    """
    Fetches sensitive data from environment variables.

    Returns:
        Dict[str, str]: A dictionary of environment variable names and their values.
    """
    load_dotenv()
    keys = ['USAJOBS_AUTHORIZATION_KEY', 'USAJOBS_USER_AGENT', 'TELEGRAM_BOT_TOKEN']
    env_vars = {key: os.getenv(key) for key in keys}

    if not all(env_vars.values()):
        logging.error("Authorization key, User-Agent, and/or Bot token not set. Exiting.")
        sys.exit(1)

    return env_vars

def save_to_json(data_dict: dict, filename: str) -> None:
    """
    Saves the given dictionary to a JSON file.

    Parameters:
        data_dict (dict): The dictionary to save.
        filename (str): The name of the file to save the dictionary in.
    """
    path = Path("data") / filename
    try:
        with path.open('w', encoding='utf-8') as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=4)
        logging.info("Data successfully saved to %s.", filename)
    except FileNotFoundError:
        logging.error("File %s not found.", filename)
    except json.JSONDecodeError:
        logging.error("Failed to save data to %s due to JSON encoding error.", filename)
    except IOError as e:
        logging.error("IOError occurred while saving data to %s: %s", filename, e)

def load_from_json(filename: str) -> dict:
    """
    Loads a dictionary from a JSON file.

    This function attempts to read a JSON file and convert it to a dictionary. 
    If the file does not exist, or if there is an error in reading the file, 
    an empty dictionary will be returned and an appropriate log message will be generated.

    Parameters:
        filename (str): The name of the JSON file to load.

    Returns:
        dict: The dictionary loaded from the JSON file,
        or an empty dictionary if the load operation fails.
    """
    path = Path("data") / filename
    try:
        with path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning("%s not found. Starting with an empty dictionary.", filename)
        return {}
    except json.JSONDecodeError:
        logging.error("%s has an invalid format. Starting with an empty dictionary.", filename)
        return {}
    except IOError as error:
        logging.error("IOError occurred while loading data from %s: %s", filename, error)
        return {}
    