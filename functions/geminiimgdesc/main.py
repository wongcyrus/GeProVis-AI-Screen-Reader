import os
import datetime
import functions_framework
import base64
import magic
from urllib.request import urlopen
import hashlib
import vertexai

# from vertexai.vision_models import ImageTextModel, Image
from vertexai.preview.generative_models import GenerativeModel, Part
from google.cloud import translate
from google.cloud import datastore


def get_user_id_by_api_key(key: str) -> str:
    client = datastore.Client(project=os.environ.get("GCP_PROJECT"))
    user = client.get(client.key("ApiKey", key))
    return str(user["user_id"])


def get_image_caption(hash: str, lang: str):
    client = datastore.Client(project=os.environ.get("GCP_PROJECT"))
    caption = client.get(client.key("Caption", hash + "->" + lang))
    return caption


def save_image_caption(
    hash: str, url: str, caption: str, lang: str, time: datetime
) -> bool:
    client = datastore.Client(project=os.environ.get("GCP_PROJECT"))
    key = client.key("Caption", hash + "->" + lang)
    entity = datastore.Entity(key=key)
    entity.update({"url": url, "caption": caption, "lang": lang, "time": time})
    client.put(entity)


@functions_framework.http
def geminiimgdesc(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """

    if request.method == "OPTIONS":
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "3600",
        }
        return ("", 204, headers)

    # Set CORS headers for the main request
    headers = {"Access-Control-Allow-Origin": "*"}

    request_json = request.get_json(silent=True)
    request_args = request.args

    key = request_args["key"]
    print(f"key: {key}")

    user_id = get_user_id_by_api_key(key)
    print(f"user_id: {user_id}")

    DEFAULT_LANG = "en-US"

    def get_value(key, default=None):
        if request_json and key in request_json:
            return request_json[key]
        elif request_args and key in request_args:
            return request_args[key]
        else:
            return default

    img = get_value("img")
    url = get_value("url")
    lang = get_value("lang", DEFAULT_LANG)

    if url:
        b64ImgData = base64.b64encode(urlopen(url).read())
        imgData = base64.decodebytes(b64ImgData)

    if img:
        imgData = base64.decodebytes(img.encode("utf-8"))

    hash_object = hashlib.sha256(imgData)
    hash = hash_object.hexdigest()

    capture = get_image_caption(hash, lang)
    if capture:
        print("From Datastore:" + capture["caption"])
        return ([capture["caption"]], 200, headers)

    mime_type = magic.from_buffer(imgData, mime=True)
    source_image = Part.from_data(imgData, mime_type=mime_type)

    # constants to use in this function
    PROJECT_ID = os.environ.get("GCP_PROJECT")
    REGION = os.environ.get("MODEL_REGION")
    MODEL_NAME = os.environ.get("MODEL_NAME")

    vertexai.init(project=PROJECT_ID, location=REGION)
    model = GenerativeModel(MODEL_NAME)
    responses = model.generate_content(
        [
            source_image,
            """Exactly not more than 40 words, describe what is the image about.""",
        ],
        generation_config={
            "max_output_tokens": 40,  # 30 words
            "temperature": 0.4,
            "top_p": 1,
            "top_k": 32,
        },
        stream=True,
    )

    # speechText = f"An image: {captions[0]}"
    speech_text = ""
    for response in responses:
        for candidate in response.candidates:
            for content_part in candidate.content.parts:
                speech_text += content_part.text
    #   speech_text = response.candidates[0].content.parts[0].text

    print(response._raw_response.usage_metadata)

    print(speech_text)
    ret_text = speech_text
    if lang != "en-US":
        client = translate.TranslationServiceClient()
        translatedText = client.translate_text(
            contents=[speech_text],
            target_language_code=lang,
            parent=f"projects/{PROJECT_ID}/locations/{REGION}",
            source_language_code="en-US",
        )
        # speechText = translatedText.translated_text
        ret_text = ""
        for translation in translatedText.translations:
            ret_text += "{}".format(translation.translated_text)
        #     speech_text = u"{}".format(translation.translated_text)
        #     break
    now = datetime.datetime.now()        
    save_image_caption(hash, url, ret_text, lang, now)

    return ([ret_text], 200, headers)
