import os
import subprocess
import datetime
import boto3
import requests
from botocore.exceptions import NoCredentialsError
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DB_NAME = "my_portfolio_db"
DB_USER = "postgres"
DB_PASSWORD = "123456789.10"
DB_HOST = "localhost"

AWS_BUCKET_NAME = "my-local-bucket"
AWS_ACCESS_KEY = "minioadmin"
AWS_SECRET_KEY = "minioadmin"
MINIO_ENDPOINT = "http://localhost:9000"

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1518262388732989496/ds_zXSlxdpOh4R0Um9uaZZweMWSWKCP4szab-ym7lpF5ArpAkW-frQAsxFtyxQEXaWP_"

current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
backup_file = f"backup_{DB_NAME}_{current_time}.dump"

def send_discord_notification(message):
    payload = {"content": message}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, verify=False)
        if response.status_code != 204:
            print(f"Discord error: {response.status_code}")
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")

def run_backup():
    print("🚀 Starting automation process...")
    
    try:
        os.environ['PGPASSWORD'] = DB_PASSWORD
        dump_command = f"pg_dump -h {DB_HOST} -U {DB_USER} -F c -b -v -f {backup_file} {DB_NAME}"
        subprocess.run(dump_command, shell=True, check=True, stdout=subprocess.DEVNULL)
        print("✅ Database exported and compressed successfully.")
    except subprocess.CalledProcessError as e:
        error_msg = f"❌ **IT ALERT:** Backup failed during SQL export.\n**Error:** {e}"
        print(error_msg)
        send_discord_notification(error_msg)
        return

    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            endpoint_url=MINIO_ENDPOINT
        )
        print("☁️ Uploading backup to Local MinIO...")
        s3.upload_file(backup_file, AWS_BUCKET_NAME, backup_file)
        
        success_msg = f"✅ **IT SYSTEM: Backup Successful**\n**File:** `{backup_file}`\n**Status:** Safely stored in Local MinIO."
        send_discord_notification(success_msg)
        print("🎉 Process completed successfully.")
    except NoCredentialsError:
        print("❌ MinIO Error: Invalid credentials.")
        send_discord_notification("❌ **IT ALERT:** Invalid MinIO credentials. File upload failed.")
    except Exception as e:
        print(f"❌ Actual MinIO Upload Error: {e}")
        send_discord_notification(f"❌ **IT ALERT:** Unexpected error during cloud upload.\n**Details:** {e}")
    finally:
        if os.path.exists(backup_file):
            os.remove(backup_file)
            print("🧹 Local cleanup completed.")

if __name__ == "__main__":
    run_backup()