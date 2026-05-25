import base64
from pathlib import Path

import requests

from config import PRINTIFY_API_TOKEN, PRINTIFY_API_BASE


def get_headers():
    if not PRINTIFY_API_TOKEN:
        raise ValueError("Missing PRINTIFY_API_TOKEN in .env file.")

    return {
        "Authorization": f"Bearer {PRINTIFY_API_TOKEN}",
        "Content-Type": "application/json",
    }


def printify_get(path):
    url = f"{PRINTIFY_API_BASE}{path}"
    response = requests.get(url, headers=get_headers(), timeout=60)

    if response.status_code >= 400:
        raise Exception(f"Printify GET error {response.status_code}: {response.text}")

    return response.json()


def printify_post(path, payload):
    url = f"{PRINTIFY_API_BASE}{path}"
    response = requests.post(url, headers=get_headers(), json=payload, timeout=120)

    if response.status_code >= 400:
        raise Exception(f"Printify POST error {response.status_code}: {response.text}")

    return response.json()


def upload_image_to_printify(file_path):
    """
    Uploads a local PNG/JPG to Printify and returns the uploaded image response.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Design file not found: {file_path}")

    with open(file_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    payload = {
        "file_name": file_path.name,
        "contents": encoded_image
    }

    return printify_post("/uploads/images.json", payload)