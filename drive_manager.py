from io import FileIO

from googleapiclient.http import MediaIoBaseDownload

from google_auth import get_drive


class DriveManager:
    def __init__(self):
        self.drive = get_drive()

    def list_folders(self):
        query = (
            "mimeType='application/vnd.google-apps.folder' "
            "and trashed=false"
        )

        results = self.drive.files().list(
            q=query,
            fields="files(id,name)"
        ).execute()

        folders = results.get("files", [])

        return [
            {
                "title": folder["name"],
                "id": folder["id"]
            }
            for folder in folders
        ]

    def list_images(self, folder_id):
        print("list_images() started")
        print("Folder ID:", folder_id)

        query = (
            f"'{folder_id}' in parents "
            "and trashed=false "
            "and mimeType contains 'image/'"
        )

        images = []
        page_token = None

        while True:

            results = self.drive.files().list(
                q=query,
                fields="nextPageToken, files(id,name,mimeType)",
                pageSize=1000,
                pageToken=page_token
            ).execute()

            files = results.get("files", [])

            print("Google Drive returned", len(files), "files")

            for file in files:
                images.append({
                    "title": file["name"],
                    "id": file["id"]
                })

            page_token = results.get("nextPageToken")

            if page_token is None:
                break

        print("Images found:", len(images))

        return images
    def download_file(self, file_id, save_path):
        try:
            request = self.drive.files().get_media(fileId=file_id)

            with FileIO(save_path, "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)

                done = False
                while not done:
                    status, done = downloader.next_chunk()

            return True

        except Exception as e:
            print(f"Failed to download {save_path}")
            print(e)
            return False