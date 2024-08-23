import sys
import webbrowser
from urllib.parse import urlparse, parse_qs
import requests
import base64
import time
import environ
from pathlib import Path

from data.models import AuthToken

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


def update_app_code(code, client_id):
    auth_token = AuthToken.objects.get(client_id=client_id)
    auth_token.app_code = code
    auth_token.save()


def get_access_token(client_id, client_secret, code, redirect_uri):
    print("Getting new access tokens")
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
        return token_data.get('access_token'), token_data.get('refresh_token'), token_data.get("expires_in")
    else:
        print(f"Failed to get access token. Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 400 and "invalid_grant" in response.text:
            # Reauthenticate to get a new authorization code
            print("Authorization code is invalid or expired. Redirecting to reauthenticate...")

            auth_url = f"https://api.enphaseenergy.com/oauth/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"

            print(f"Go to the following url and get a new auth code:\n")
            print(auth_url)
            new_code = input("\nEnter the new authorization code: ")

            update_app_code(new_code, client_id)

            if new_code.lower() == 'q':
                print("Exiting the process as requested.")
                sys.exit(0)

            return get_access_token(client_id, client_secret, new_code, redirect_uri)
        else:
            return None, None, None


def refresh_access_token(client_id, client_secret, refresh_token, app):
    print("Refreshing access tokens")
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
    elif response.status_code == 401:
        app.access_token, app.refresh_token, app.expires_in = get_access_token(
                                                                                client_id,
                                                                                client_secret,
                                                                                app.app_code,
                                                                                app.redirect_uri
                                                                              )

        if not all([app.access_token, app.refresh_token, app.expires_in]):
            raise Exception(
                f"get_access_token did not return valid tokens. "
                f"Access Token: {app.access_token}, Refresh Token: {app.refresh_token}, Expires In: {app.expires_in}"
            )

        if not app.access_token and not app.refresh_token and not app.expires_in:
            raise Exception(
                f"Unable to refresh the tokens. "
                f"Status Code: {response.status_code}, Response: {response.text}, "
                f"Client ID: {client_id}, App Code: {app.app_code}, Redirect URI: {app.redirect_uri}"
            )
        app.save()
        return app.access_token, app.refresh_token, app.expires_in
    else:
        raise Exception(f"Failed to refresh token. Status: {response.status_code}, Response: {response.text}")


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