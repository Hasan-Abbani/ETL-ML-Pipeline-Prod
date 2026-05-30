import requests
import os
from dotenv import load_dotenv
load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")

url = "https://api.wattics.com/api/v1/meters?organization_id=63&site_id=106"

payload = ""
headers = {
    'Content-Type': "application/json",
    'Authorization': os.getenv("API_TOKEN"),
    }

response = requests.request("GET", url, data=payload, headers=headers)

print(response.text)