import requests
import os

url = "https://api.wattics.com/api/v1/sites?organization_id=1"

payload = ""
headers = {
    'Content-Type': "application/json",
    'Authorization': "YOUR_API_TOKEN_HERE",
    }

response = requests.request("GET", url, data=payload, headers=headers)

print(response.text)