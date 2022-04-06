from __future__ import print_function
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import requests
import sys
import time
import os
import filelock
from datetime import datetime

ALBUMTITLE = "Fujifilm";

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly',
          'https://www.googleapis.com/auth/photoslibrary.sharing']

def get_file_list_in_directory_by_extension(mypath, ext):
    return [os.path.join(mypath, f) for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f)) and f.endswith(ext)]


def move_one_file_to_cloud(creds, albumId, file_to_upload_full_path):
    print('Uploading {}'.format(file_to_upload_full_path))
    file_to_upload_name = os.path.basename(file_to_upload_full_path)
    file_to_upload_mtime = os.path.getmtime(file_to_upload_full_path)
    headers = {
    'Content-Type': "application/octet-stream",
    'X-Goog-Upload-File-Name': file_to_upload_name,
    'X-Goog-Upload-Protocol': "raw",
    'Authorization': "Bearer " + creds.token,
    }
     
    data = open(file_to_upload_full_path, 'rb').read()
    response = requests.post('https://photoslibrary.googleapis.com/v1/uploads', headers=headers, data=data)
    response.raise_for_status()
    image_token = response.text
    headers = {
        'Content-Type': "application/json",
        'Authorization': "Bearer " + creds.token,
        }
    reqbody = {
          'albumId': albumId,
          'newMediaItems': [
            {
              'simpleMediaItem': {
                'uploadToken': image_token
              }
            }
          ]
        }

    response = requests.post('https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate', headers=headers, json=reqbody)
    response.raise_for_status()
    # print('Response: {}'.format(response))


def main():
    script_workdir = os.path.dirname(os.path.realpath(__file__))
    credentials_token_path = os.path.join(script_workdir, 'token.pickle')
    credentials_json_path = os.path.join(script_workdir, 'credentials.json') 
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(credentials_token_path):
        with open(credentials_token_path, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_json_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(credentials_token_path, 'wb') as token:
            pickle.dump(creds, token)

    service = build('photoslibrary', 'v1', credentials=creds)
    results = service.albums().list(
        pageSize=10, fields="nextPageToken,albums(id,title)").execute()
    albumId = None
    items = results.get('albums', [])
    if items:
        for item in items:
            # print('{0} ({1})'.format(item['title'], item['id']))
            if item['title'] == ALBUMTITLE:
                albumId = item['id']
    
    if albumId == None:
        response_create_album = service.albums().create(body={'album':{'title':ALBUMTITLE, 'isWriteable': 'true'}}).execute()
        albumId = response_create_album['id']
        headers = {
        'Content-Type': "application/json",
        'Authorization': "Bearer " + creds.token,
        }
        reqbody = {
        "sharedAlbumOptions": {
        "isCollaborative": "true",
        "isCommentable": "true"
        }
        }
        response = requests.post('https://photoslibrary.googleapis.com/v1/albums/{}:share'.format(response_create_album['id']), headers=headers, json=reqbody)
        response.raise_for_status()
        
    if len(sys.argv) > 1:
        """
        wait a minute if the file hasn't been created yet
        """
        for i in range(1, len(sys.argv)):
            file_to_upload_full_path = sys.argv[i]
            start = time.time()
            while time.time() - start < 60:
                if os.path.isfile(file_to_upload_full_path):
                    break
                else:
                    time.sleep(1)
            file_to_upload_dir_path = os.path.dirname(os.path.realpath(file_to_upload_full_path))
            file_to_upload_mtime = os.path.getmtime(file_to_upload_full_path)
            move_one_file_to_cloud(creds, albumId, file_to_upload_full_path)


if __name__ == '__main__':
    file_lock_path = "//tmp//photos.py.lock"
    lock = filelock.FileLock(file_lock_path)
    try:
        with lock.acquire(timeout=1):
            main()
            lock.release()
    except filelock.Timeout:
        print('{} is locked. Is another instance running?'.format(file_lock_path))
        pass
