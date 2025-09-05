import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = "service_account.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]

def connect_to_drive():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError("Le fichier de credentials n'existe pas !")
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("drive", "v3", credentials=creds)
    return service

if __name__ == "__main__":
    try:
        service = connect_to_drive()
        print("Connexion réussie à Google Drive !")

        # Chercher le dossier Airflow
        results = service.files().list(
            q="name='Airflow' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces="drive",
            fields="files(id, name)"
        ).execute()

        folders = results.get("files", [])
        if not folders:
            print(" Le dossier 'Airflow' n'a pas été trouvé.")
        else:
            folder_id = folders[0]["id"]
            print(f" Dossier 'Airflow' trouvé (ID: {folder_id})")

            # Lister les fichiers à l'intérieur
            files = service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                spaces="drive",
                fields="files(id, name)"
            ).execute().get("files", [])

            if not files:
                print(" Aucun fichier dans le dossier 'Airflow'.")
            else:
                print(" Fichiers dans 'Airflow' :")
                for f in files:
                    print(f"- {f['name']} (ID: {f['id']})")

    except Exception as e:
        print(f" Erreur : {e}")
