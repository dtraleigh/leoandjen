from urllib.parse import urlparse, parse_qs
import requests
import base64
import time
import environ
from pathlib import Path

env = environ.Env(DEBUG=(bool, False))
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(BASE_DIR / ".env")


def get_auth_code(auth_url):
    # Print the Auth URL for the HO
    print(f"Please ask the Homeowner to visit the following URL to authorize the application:\n{auth_url}")

    # Assuming HO approves and is redirected back to the redirect_uri with the auth code
    redirect_uri = input("After the Homeowner approves, enter the URL they were redirected to: ")

    # Parse the redirect_uri to extract the auth code
    parsed_url = urlparse(redirect_uri)
    query_params = parse_qs(parsed_url.query)
    code = query_params.get('code')

    if code:
        return code[0]
    else:
        print("Error: Authorization code not found in the redirect URI.")
        return None


def get_access_token(client_id, client_secret, code, redirect_uri):
    # Encode client_id and client_secret for the Authorization header
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    # Define the payload for the POST request
    payload = {
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
        'code': code
    }

    # Define the headers with the Authorization header
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Make the POST request to obtain the access token
    response = requests.post('https://api.enphaseenergy.com/oauth/token', data=payload, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        return access_token, refresh_token
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None, None


def refresh_access_token(client_id, client_secret, refresh_token, app):
    # Encode client_id and client_secret for the Authorization header
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    # Define the payload for the POST request to refresh the access token
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }

    # Define the headers with the Authorization header
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Make the POST request to refresh the access token
    response = requests.post('https://api.enphaseenergy.com/oauth/token', data=payload, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        token_data = response.json()
        app.access_token = token_data.get("access_token")
        app.refresh_token = token_data.get("refresh_token")
        app.expires_in = token_data.get("expires_in")
        app.save()
        return app.access_token, app.refresh_token
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None, None


def is_token_expired(auth_data):
    current_time = int(time.time())
    expiration_timestamp = auth_data.issued_datetime.timestamp() + auth_data.expires_in

    if current_time >= expiration_timestamp:
        return True
    else:
        return False


def get_site_production(token, start_date, end_date):
    url = f"https://api.enphaseenergy.com/api/v4/systems/3861048/energy_lifetime?key" \
          f"={env('ENPHASE_API_KEY')}&start_date={start_date}&end_date={end_date}"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.request("GET", url, headers=headers, data={})

    return response.json()


def get_production_amts(site_data):
    try:
        return site_data["production"]
    except KeyError:
        print(f"Issue getting production amounts\n{site_data}")
        return []