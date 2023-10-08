import logging
import os
import sys
from typing import Dict
from pathlib import Path
import json
from dotenv import load_dotenv

def init_logging() -> None:
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

def fetch_environment_variables() -> Dict[str, str]:
    """
    Fetches sensitive data from environment variables.

    Returns:
        Dict[str, str]: A dictionary of environment variable names and their values.
    """
    load_dotenv()
    env_vars = {}
    env_vars['USAJOBS_AUTHORIZATION_KEY'] = os.environ.get('USAJOBS_AUTHORIZATION_KEY')
    env_vars['USAJOBS_USER_AGENT'] = os.environ.get('USAJOBS_USER_AGENT')
    env_vars['TELEGRAM_BOT_TOKEN'] = os.environ.get('TELEGRAM_BOT_TOKEN')

    if not env_vars['USAJOBS_AUTHORIZATION_KEY'] or not env_vars['USAJOBS_USER_AGENT'] or not env_vars['TELEGRAM_BOT_TOKEN']:
        logging.error("Authorization key, User-Agent, and/or Bot token not set. Exiting.")
        sys.exit(1)

    return env_vars

def save_to_json(data_dict: dict, filename: str) -> None:
    """
    Saves the given dictionary to a JSON file.

    Parameters:
        data_dict (dict): The dictionary to save.
        filename (str): The name of the file to save the dictionary in.

    Returns:
        bool: True if the save operation was successful, False otherwise.
    """
    path = Path("data") / filename
    try:
        with path.open('w', encoding='utf-8') as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=4)
        logging.info("Data successfully saved to %s.", filename)
    except Exception as e:
        logging.error("Failed to save data to %s: %s", filename, e)

def load_from_json(filename: str) -> dict:
    """
    Loads a dictionary from a JSON file.

    This function attempts to read a JSON file and convert it to a dictionary. 
    If the file does not exist, or if there is an error in reading the file, 
    an empty dictionary will be returned and an appropriate log message will be generated.

    Parameters:
        filename (str): The name of the JSON file to load.

    Returns:
        dict: The dictionary loaded from the JSON file, or an empty dictionary if the load operation fails.
    """
    path = Path("data") / filename
    try:
        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        logging.warning("%s not found. Starting with an empty dictionary.", filename)
        return {}
    except json.JSONDecodeError:
        logging.error("%s has an invalid format. Starting with an empty dictionary.", filename)
        return {}
    except Exception as error:
        logging.error("Failed to load data from %s: %s", filename, error)
        return {}
    