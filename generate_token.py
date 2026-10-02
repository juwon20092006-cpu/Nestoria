import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import json

# For sending email via Gmail API, this scope is sufficient
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def main():
    creds = None

    # If token.json exists, load it
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no valid credentials, run authorization flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            # This opens your browser for authorization
            creds = flow.run_local_server(port=8080)

        # Save credentials for next use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    print("✅ Authorization successful!")
    print("token.json generated")

    # Verify refresh token exists
    with open('token.json') as f:
        data = json.load(f)
    print(f"has refresh_token: {'refresh_token' in data}")

if __name__ == '__main__':
    main()