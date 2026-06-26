import os
import sys
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def get_credentials():

    creds = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as f:
            creds = pickle.load(f)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    else:
        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        client_secret_path = os.path.join(
            base_path,
            "client_secrets.json"
        )

        print("CLIENT SECRET FILE =", client_secret_path)

        flow = InstalledAppFlow.from_client_secrets_file(
            client_secret_path,
            SCOPES
        )

        creds = flow.run_local_server(
            host="localhost",
            port=0,
            open_browser=True
        )

    with open("token.pickle", "wb") as f:
        pickle.dump(creds, f)

    return creds


def get_drive():
    creds = get_credentials()
    return build("drive", "v3", credentials=creds)