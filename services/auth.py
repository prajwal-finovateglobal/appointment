import os
import json
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# OAuth2 scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']


class PersistentCalendarService:
    def __init__(self, credentials_file):
        self.credentials_file = credentials_file
        
    def get_service(self):
        """Get Calendar service with automatic token refresh"""
        creds = self._load_credentials()
        
        # This automatically refreshes if needed and resets the 6-month timer
        if creds.expired:
            creds.refresh(Request())
            self._save_credentials(creds)
            
        return build('calendar', 'v3', credentials=creds)
    
    def _load_credentials(self):
        with open(self.credentials_file, 'r') as f:
            cred_data = json.load(f)
            
        return Credentials(
            token=cred_data['token'],
            refresh_token=cred_data['refresh_token'],
            token_uri=cred_data['token_uri'],
            client_id=cred_data['client_id'],
            client_secret=cred_data['client_secret'],
            scopes=cred_data['scopes']
        )
    
    def _save_credentials(self, creds):
        cred_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        
        with open(self.credentials_file, 'w') as f:
            json.dump(cred_data, f)


# Initialize the persistent calendar service
script_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to mcp_server_calender directory
parent_dir = os.path.dirname(script_dir)
print(f"Parent directory: {parent_dir}")
credentials_path = os.path.join(parent_dir, 'credentials.json')
print(f"Credentials path: {credentials_path}")
calendar_service = PersistentCalendarService(credentials_path)

def get_authenticated_service():
    """Get authenticated Google Calendar service using persistent authentication"""
    try:
        return calendar_service.get_service()
    except Exception as e:
        print(f" Authentication error: {e}")
        return None
