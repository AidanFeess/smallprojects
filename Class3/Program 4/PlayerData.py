import json
import os

from GameConstants import *

class PlayerData:
    def __init__(self, filename=f"{DIR_PLAYER_DATA}/player_data.json"):
        """Initialize the player data handler with a file for storing data."""
        self.filename = filename
        self.data = {
            "player_name": "Greg",
            "level": 1,
            "high_score": 0,
        }
        self.load_data()

    def save_data(self):
        """Saves the current player data to a JSON file."""
        try:
            with open(self.filename, 'w') as file:
                json.dump(self.data, file, indent=4)
            print(f"Player data successfully saved to {self.filename}")
        except Exception as e:
            print(f"Error saving data: {e}")

    def load_data(self):
        """Loads player data from the JSON file, if it exists."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as file:
                    self.data = json.load(file)
                print(f"Player data successfully loaded from {self.filename}")
            except Exception as e:
                print(f"Error loading data: {e}")
        else:
            print("No existing player data found. Starting with default data.")
            self.save_data()

    def update_data(self, key, value):
        """Updates a specific key in the player data and saves the file."""
        keys = key.split(".")
        d = self.data
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value
        self.save_data()

    def get_data(self, key):
        """Retrieves a specific piece of player data using dot notation."""
        keys = key.split(".")
        d = self.data
        for k in keys:
            d = d.get(k, None)
            if d is None:
                return None
        return d

    def update_high_score(self, score):
        """Updates the high score if the new score is higher."""
        if score > self.data["high_score"]:
            self.data["high_score"] = score
            self.save_data()

    def reset_data(self):
        """Resets the player data to default values and saves it."""
        self.data = {
            "player_name": "Hero",
            "level": 1,
            "high_score": 0,
        }
        self.save_data()