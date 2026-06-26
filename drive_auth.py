from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Read-only access to Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def connect_google_drive():
    """
    Authenticates the user and returns the Google Drive service object.
    """

    creds = None

    # Load saved token
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # Login if required
    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json",
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        # Save token
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("drive", "v3", credentials=creds)

    return service