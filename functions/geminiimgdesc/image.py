import hashlib
import os
import base64
import vertexai

import requests
from PIL import Image
import io

from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import HumanMessage
from langchain_google_vertexai import ChatVertexAI


GCP_PROJECT = os.environ.get("GCP_PROJECT")
MODEL_REGION = os.environ.get("MODEL_REGION")
MODEL_NAME = os.environ.get("MODEL_NAME")


REGION_RATE_LIMIT = {
    "us-central1": 100,
    "us-east4": 60,
    "us-west1": 60,
    "us-west4": 60,
    "northamerica-northeast1": 60,
    "europe-west1": 60,
    "europe-west2": 60,
    "europe-west3": 60,
    "europe-west3": 60,
    "europe-west9": 60,
    "asia-northeast1": 60,
    "asia-northeast3": 60,
    "asia-southeast1": 60,
}


def download_and_resize_image(url, max_size=3 * 1024 * 1024) -> str:
    # Download the image
    response = requests.get(url)
    img = Image.open(io.BytesIO(response.content))
    hashed_url = hashlib.sha256(url.encode()).hexdigest()
    file_path = os.path.join("/tmp", hashed_url + ".png")

    byte_arr = io.BytesIO()
    # Check the original image size
    original_size = len(response.content)
    if original_size <= max_size:
        img.save(byte_arr, format="PNG")
    else:
        print(f"Resize Original image size: {original_size}")
        # Calculate the resize ratio
        resize_ratio = (max_size / original_size) ** 0.5

        # Resize the image
        new_size = (int(img.width * resize_ratio), int(img.height * resize_ratio))
        resized_img = img.resize(new_size)

        # Convert the image back to bytes
        resized_img.save(byte_arr, format="PNG")
        resized_bytes = byte_arr.getvalue()
        print(f"Resized image size: {len(resized_bytes)}")

    with open(file_path, "wb") as f:
        f.write(byte_arr.getvalue())
    return file_path


def generate_image_description(url: str, lang: str, model_region: str):
    file_path = download_and_resize_image(url)
    with open(file_path, "rb") as image_file:
        image_bytes = image_file.read()

    vertexai.init(project=GCP_PROJECT, location=model_region)

    llm = ChatVertexAI(
        model_name="gemini-pro-vision",
        temperature=0.4,
        max_output_tokens=40,
        top_p=1,
        top_k=32,
    )

    image_message = {
        "type": "image_url",
        "image_url": {
            "url": f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"
        },
    }
    text_message = {
        "type": "text",
        "text": f"""Describes the image in less than 40 words in {lang}.""",
    }
    message = HumanMessage(content=[text_message, image_message])

    output = llm([message])
    print(output.content)
    return output.content