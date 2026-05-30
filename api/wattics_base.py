import requests
import os 
from dotenv import load_dotenv
load_dotenv()

class WatticsBaseClient:
    def __init__(self, api_token):
        self.base_url = "https://api.wattics.com/api/v1"
        self.headers = {
            "Content-Type": "application/json",
            'Authorization': os.getenv("API_TOKEN"),
        }

    def get(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"

        response = requests.get(
            url,
            headers=self.headers,
            params=params
        )

        if response.status_code != 200:
            print(f"API request failed: {url}")
            print(f"Status code: {response.status_code}")
            print(response.text)
            return None

        return response.json()# convert from json string to python dict 