import requests
import json

AUTH_TOKEN = "55c1fec958f3c7a0-51da758222497544-6c70a67feb04331e"

API_URL_INFO = "https://chatapi.viber.com/pa/get_account_info"

headers = {
    'X-Viber-Auth-Token': AUTH_TOKEN,
    'Content-Type': 'application/json'
}

try:
    response = requests.post(API_URL_INFO, headers=headers)
    response.raise_for_status()
    account_info = response.json()
    
    if account_info.get('status') == 0:
        print("Successfully retrieved account info:")
        # The 'id' field in the response is the Channel ID (Public Account ID)
        print(f"Channel ID (Public Account ID): {account_info.get('id')}") 
        print(f"Channel Name: {account_info.get('name')}")
        print(f"Details: {json.dumps(account_info, indent=4)}")
    else:
        print(f"Failed to get account info. Status: {account_info.get('status')}, Message: {account_info.get('status_message')}")

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
