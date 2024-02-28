import os
import random
from time import sleep
import functions_framework
import hashlib

from .datastore import (
    get_usages_by_region,
    get_user_id_by_api_key,
    get_image_caption,
    save_data,
    get_usages_by_user_id,
)
from .image import generate_image_description, REGION_RATE_LIMIT


GCP_PROJECT = os.environ.get("GCP_PROJECT")
DAILY_BUDGET = os.environ.get("DAILY_BUDGET")
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


def get_user_id(request, request_args):
    key = request.headers.get("X-API-Key")
    if not key:
        key = request_args["key"]
    print(f"key: {key}")
    user_id = get_user_id_by_api_key(key)
    print(f"user_id: {user_id}")
    return user_id


def get_url_hash_and_locale(request_json, request_args):
    url = get_value(request_json, request_args, "url")
    hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
    locale = get_value(request_json, request_args, "lang", DEFAULT_LANG)
    return url, hash, locale


@functions_framework.http
def geminiimgdesc(request):
    headers = handle_cors(request)
    request_json, request_args = get_request_data(request)
    user_id = get_user_id(request, request_args)

    current_cost = get_usages_by_user_id(user_id)

    url, hash, locale = get_url_hash_and_locale(request_json, request_args)
    capture = get_image_caption(hash, DEFAULT_LANG)

    if capture:
        print("From Datastore:" + capture["caption"])
        return ([capture["caption"]], 200, headers)

    print(f"current_cost: {current_cost}")
    if current_cost > float(DAILY_BUDGET):
        return (
            [f"You have exceeded the limit of {DAILY_BUDGET} USD per day"],
            403,
            headers,
        )

    for i in range(3):
        # REGION_RATE_LIMIT random pick on as model region
        model_region = random.choice(list(REGION_RATE_LIMIT.keys()))
        last_minute_call_count = get_usages_by_region(model_region)
        if (REGION_RATE_LIMIT[model_region] - 2) > last_minute_call_count:
            break
        sleep(i * random.randint(1, 2))
    else:
        return (
            [f"Overloaded, please try again later"],
            503,
            headers,
        )

    ret_text = generate_image_description(url, locale, model_region)
    save_data(user_id, hash, ret_text, locale, model_region)

    return ([ret_text], 200, headers)
