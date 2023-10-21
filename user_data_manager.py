import json
from typing import Dict, Optional, Any

class UserDataManager:
    """Manages persistence of user data in JSON file."""
    def __init__(self, file_path: str) -> None:
        """Initializes the data manager."""
        self.file_path = file_path
        self.user_data_dict = self.load_data()

    def load_data(self) -> Dict[str, Any]:
        """Loads user data from JSON file."""
        try:
            with open(self.file_path, 'r', encoding='UTF-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading user data: {e}")
            return {}

    def save_data(self, data: Dict[str, Any]) -> None: 
        """Saves user data to JSON file."""
        try:
            with open(self.file_path, 'w', encoding='UTF-8') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving user data: {e}")

    def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Gets data for a user."""
        return self.user_data_dict.get(user_id)

    def update_user_data(self, user_id: str, data: Dict[str, Any]) -> None:
        """Updates data for a user."""
        self.user_data_dict[user_id] = data
        self.save_data(self.user_data_dict)
