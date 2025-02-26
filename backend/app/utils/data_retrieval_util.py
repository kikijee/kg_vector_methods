from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.auth import ServiceAccountCredentials
import io

# Path to your service account JSON key file
SERVICE_ACCOUNT_FILE = r"./app/rutabaga-pipline-poc-key.json"

# Define scope and authenticate
SCOPES = ["https://www.googleapis.com/auth/drive"]
gauth = GoogleAuth()
gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPES)

# Initialize the Drive API
drive = GoogleDrive(gauth)

FOLDER_ID = "1dv9iRTypfvkV6PwHIU3X_-Q1c86Qveg8"

def list_files_in_folder(folder_id):
    query = f"'{folder_id}' in parents and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()
    return file_list

# List all files
files = list_files_in_folder(FOLDER_ID)
for file in files:
    print(f"File Name: {file['title']}, File ID: {file['id']}")

def read_text_file(file):
    content = file.GetContentString()  # Read file as a string
    return content

# Read text files from Drive
for file in files:
    if file['title'].endswith(('.txt', '.csv', '.json')):  # Filter for text-based files
        print(f"Reading {file['title']}")
        file_content = read_text_file(file)
        print(f"Content Preview:\n{file_content[:200]}...\n")  # Print first 200 characters

