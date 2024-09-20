import os
import datetime
from google.cloud import firestore


def get_entity_from_firestore(collection: str, document_id: str):
    client = firestore.Client(database="aireader")
    doc_ref = client.collection(collection).document(document_id)
    doc = doc_ref.get()
    return doc.to_dict() if doc.exists else None


def save_entity_to_firestore(collection: str, document_id: str, data: dict):
    client = firestore.Client(database="aireader")
    doc_ref = client.collection(collection).document(document_id)
    doc_ref.set(data)


def get_user_id_by_api_key(key: str) -> str:
    user = get_entity_from_firestore("ApiKey", key)
    return str(user["user_id"]) if user else None


def get_image_caption(hash: str, lang: str = None):
    if lang is None:
        return get_entity_from_firestore("Caption", hash)
    return get_entity_from_firestore("Caption", hash + "->" + lang)


def save_image_caption_for_lang(hash: str, caption: str, lang: str):
    now = datetime.datetime.now()
    save_entity_to_firestore(
        "Caption",
        hash + "->" + lang,
        {"caption": caption, "lang": lang, "time": now},
    )


def save_image_caption(hash: str, caption: str, lang: str, now: datetime = datetime.datetime.now()):   
    save_entity_to_firestore(
        "Caption",
        hash + "->" + lang,
        {"caption": caption, "lang": lang, "time": now},
    )


def save_usage(
    user_id: str,
    hash: str,
    text_input: str,
    text_output: str,
    model_region: str,
    now: datetime,
):
    cost = (
        0.0025 + 0.000125 * len(text_input) / 1000 + 0.000375 * len(text_output) / 1000
    )
    save_entity_to_firestore(
        "Usage",
        user_id + "->" + hash,
        {
            "user_id": user_id,
            "text_input": text_input,
            "text_output": text_output,
            "cost": cost,
            "model_region": model_region,
            "time": now,
        },
    )


def save_data(user_id, hash, ret_text, locale, model_region):
    now = datetime.datetime.now()
    save_image_caption(hash, ret_text, locale, now)
    save_usage(
        user_id,
        hash,
        f"Describes the image in less than 40 words in {locale}",
        ret_text,
        model_region,
        now,
    )


def get_usages_by_user_id(user_id: str):
    client = firestore.Client(database="aireader")
    user_query = client.collection("Usage").where("user_id", "==", str(user_id)).where(
        "time", ">", datetime.datetime.now() - datetime.timedelta(days=1)
    )

    total_cost = 0
    for doc in user_query.stream():
        total_cost += doc.to_dict().get("cost", 0)

    return total_cost


def get_usages_by_region(region: str):
    client = firestore.Client(database="aireader")
    region_query = client.collection("Usage").where("model_region", "==", region).where(
        "time", ">", datetime.datetime.now() - datetime.timedelta(minutes=1)
    )

    count = 0
    for _ in region_query.stream():
        count += 1

    return count