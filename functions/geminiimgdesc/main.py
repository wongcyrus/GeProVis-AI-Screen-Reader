import os
import functions_framework
import hashlib

from .datastore import get_user_id_by_api_key, get_image_caption, save_data
from .image import get_image_data, generate_image_description


GCP_PROJECT = os.environ.get("GCP_PROJECT")
MODEL_REGION = os.environ.get("MODEL_REGION")
MODEL_NAME = os.environ.get("MODEL_NAME")
DEFAULT_LANG = "en-US"


def get_value(request_json, request_args, key, default=None):
    if request_json and key in request_json:
        return request_json[key]
    elif request_args and key in request_args:
        return request_args[key]
    else:
        return default


def handle_cors(request):
    if request.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "3600",
        }
        return ("", 204, headers)
    else:
        return {"Access-Control-Allow-Origin": "*"}


def get_request_data(request):
    return request.get_json(silent=True), request.args


def get_user_key_and_id(request, request_args):
    key = request.headers.get("X-API-Key")
    if not key:
        key = request_args["key"]
    print(f"key: {key}")
    user_id = get_user_id_by_api_key(key)
    print(f"user_id: {user_id}")
    return key, user_id


def get_image_data_and_hash(request_json, request_args):
    img = get_value(request_json, request_args, "img")
    url = get_value(request_json, request_args, "url")
    imgData = get_image_data(img, url)
    hash = hashlib.sha256(imgData).hexdigest()
    return imgData, hash


@functions_framework.http
def geminiimgdesc(request):
    headers = handle_cors(request)
    request_json, request_args = get_request_data(request)
    key, user_id = get_user_key_and_id(request, request_args)
    imgData, hash = get_image_data_and_hash(request_json, request_args)
    capture = get_image_caption(hash, DEFAULT_LANG)

    if capture:
        print("From Datastore:" + capture["caption"])
        return ([capture["caption"]], 200, headers)

    ret_text = generate_image_description(imgData, DEFAULT_LANG)
    save_data(user_id, hash, ret_text, DEFAULT_LANG)

    return ([ret_text], 200, headers)
