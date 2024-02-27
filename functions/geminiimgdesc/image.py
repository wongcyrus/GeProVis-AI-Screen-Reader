import os
import base64
import magic
import vertexai

from urllib.request import urlopen
from vertexai.preview.generative_models import GenerativeModel, Part

GCP_PROJECT = os.environ.get("GCP_PROJECT")
MODEL_REGION = os.environ.get("MODEL_REGION")
MODEL_NAME = os.environ.get("MODEL_NAME")


def get_image_data(img, url):
    if url:
        b64ImgData = base64.b64encode(urlopen(url).read())
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
