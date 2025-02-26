from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.auth import ServiceAccountCredentials
import io

SERVICE_ACCOUNT_FILE = r"./rutabaga-pipline-poc-key.json"
# Define scope and authenticate
SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_ID = "1dv9iRTypfvkV6PwHIU3X_-Q1c86Qveg8"

class GoogleDriveAccess:

    def __init__(self):
        gauth = GoogleAuth()
        gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPES)

        self.folder_id = FOLDER_ID
        self.drive = GoogleDrive(gauth)

    """
    Example Usage:

    files = list_files_in_folder(FOLDER_ID)
    for file in files:
        print(f"File Name: {file['title']}, File ID: {file['id']}")
    """

    def list_files_in_folder(self):
        query = f"'{self.folder_id}' in parents and trashed=false"
        file_list = self.drive.ListFile({'q': query}).GetList()
        return file_list

    """
    Example Usage:

    for file in files:
    if file['title'].endswith(('.txt', '.csv', '.json')):  # Filter for text-based files
        print(f"Reading {file['title']}")
        file_content = read_text_file(file)
        print(f"Content Preview:\n{file_content[:200]}...\n")  # Print first 200 characters
    """

    @staticmethod
    def read_text_file(file):
        content = file.GetContentString()  # Read file as a string
        return content

def fetch_files():
    res = []
    gda = GoogleDriveAccess()
    files = gda.list_files_in_folder()

    for file in files:
        res.append({
            "page_content": gda.read_text_file(file),
            "metadata":{"file_name":file["title"]}
        })
    return res