import requests
import json

# --- Configuration ---
# Replace with your actual authentication token and sender details
AUTH_TOKEN = "55c1fec958f3c7a0-51da758222497544-6c70a67feb04331e"
SENDER_NAME = 'Graintrade.Info' # The name that will appear as the sender
SENDER_AVATAR = 'https://example.com/avatar.jpg' # Public HTTPS URL for sender avatar
# ---------------------

# Viber API Endpoint for posting messages to a public account/channel
API_URL = "https://chatapi.viber.com/pa/get_account_info"

def send_viber_message(message_text):
    """
    Sends a text message to the configured Viber channel.
    """
    headers = {
        'X-Viber-Auth-Token': AUTH_TOKEN,
        'Content-Type': 'application/json'
    }

    payload = {
        'from': AUTH_TOKEN, # In the channel API, the 'from' field is the auth token
        'sender': {
            'name': SENDER_NAME,
            'avatar': SENDER_AVATAR
        },
        'type': 'text',
        'text': message_text
    }

    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status() # Raise an exception for bad status codes (4XX or 5XX)
        result = response.json()
        
        if result['status'] == 0:
            print(f"Message sent successfully! Message Token: {result.get('message_token')}")
        else:
            print(f"Failed to send message. Status: {result['status']}, Message: {result.get('status_message')}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the API call: {e}")
    except json.JSONDecodeError:
        print("Failed to decode JSON response from Viber API.")

if __name__ == "__main__":
    # Example usage:
    post_content = "Hello channel members! This is an automated post from my Python script."
    send_viber_message(post_content)
