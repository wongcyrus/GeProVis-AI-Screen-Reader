import os
import base64
import magic
import vertexai

import requests
from PIL import Image
import io

from urllib.request import urlopen
from vertexai.preview.generative_models import GenerativeModel, Part

GCP_PROJECT = os.environ.get("GCP_PROJECT")
MODEL_REGION = os.environ.get("MODEL_REGION")
MODEL_NAME = os.environ.get("MODEL_NAME")


def download_and_resize_image(url, max_size=3*1024*1024):
    # Download the image
    response = requests.get(url)
    img = Image.open(io.BytesIO(response.content))

    # Check the original image size
    original_size = len(response.content)
    if original_size <= max_size:
        return response.content

    print(f"Resize Original image size: {original_size}")
    # Calculate the resize ratio
    resize_ratio = (max_size / original_size) ** 0.5

    # Resize the image
    new_size = (int(img.width * resize_ratio), int(img.height * resize_ratio))
    resized_img = img.resize(new_size)

    # Convert the image back to bytes
    byte_arr = io.BytesIO()
    resized_img.save(byte_arr, format='PNG')
    resized_bytes = byte_arr.getvalue()
    print(f"Resized image size: {len(resized_bytes)}")

    return resized_bytes

def get_image_data(img, url):
    if url:
        b64ImgData = base64.b64encode(download_and_resize_image(url))
        return base64.decodebytes(b64ImgData)
    elif img:
        return base64.decodebytes(img.encode("utf-8"))


def generate_image_description(imgData, lang):
    mime_type = magic.from_buffer(imgData, mime=True)
    source_image = Part.from_data(imgData, mime_type=mime_type)
    vertexai.init(project=GCP_PROJECT, location=MODEL_REGION)
    model = GenerativeModel(MODEL_NAME)
    prompt = f"""Describes the image in less than 40 words in {lang}."""
    print("Calling Model.")
    responses = model.generate_content(
        [
            source_image,
            prompt,
        ],
        generation_config={
            "max_output_tokens": 40,  # 30 words
            "temperature": 0.4,
            "top_p": 1,
            "top_k": 32,
        },
        stream=True,
    )
    speech_text = ""
    for response in responses:
        for candidate in response.candidates:
            for content_part in candidate.content.parts:
                speech_text += content_part.text
    print(response._raw_response.usage_metadata)
    print(speech_text)
    return speech_text
