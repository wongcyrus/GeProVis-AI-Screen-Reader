import os
import datetime
from google.cloud import datastore
from google.cloud.datastore.query import BaseCompositeFilter, PropertyFilter


def get_entity_from_datastore(kind: str, id: str):
    client = datastore.Client()
    return client.get(client.key(kind, id))


def save_entity_to_datastore(kind: str, id: str, data: dict):
    client = datastore.Client()
    key = client.key(kind, id)
    entity = datastore.Entity(key=key)
    entity.update(data)
    client.put(entity)


def get_user_id_by_api_key(key: str) -> str:
    user = get_entity_from_datastore("ApiKey", key)
    return str(user["user_id"])


def get_image_caption(hash: str, lang: str = None):
    if lang is None:
        return get_entity_from_datastore("Caption", hash)
    return get_entity_from_datastore("Caption", hash + "->" + lang)


def save_image_caption_for_lang(hash: str, caption: str, lang: str):
    now = datetime.datetime.now()
    save_entity_to_datastore(
        "Caption",
        hash + "->" + lang,
        {"caption": caption, "lang": lang, "time": now},
    )


def save_image_caption(hash: str, caption: str, lang: str, now: datetime):
    # save_image_caption_for_lang(hash, caption, lang, now)
    save_entity_to_datastore(
        "Caption",
        hash,
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
    save_entity_to_datastore(
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
    client = datastore.Client()
    user_query = client.query(kind="Usage")

    user_query.add_filter(
        filter=BaseCompositeFilter(
            "AND",
            [
                PropertyFilter("user_id", "=", str(user_id)),
                PropertyFilter(
                    "time", ">", datetime.datetime.now() - datetime.timedelta(days=1)
                ),
            ],
        )
    )

    user_cost_query = client.aggregation_query(query=user_query).sum(
        property_ref="cost", alias="total_cost_over_1_day"
    )

    data = list(user_cost_query.fetch())
    cost = data[0][0].value if len(data) == 1 else 0
    return cost


def get_usages_by_region(region: str):
    client = datastore.Client()
    user_query = client.query(kind="Usage")

    user_query.add_filter(
        filter=BaseCompositeFilter(
            "AND",
            [
                PropertyFilter("model_region", "=", region),
                PropertyFilter(
                    "time", ">", datetime.datetime.now() - datetime.timedelta(minutes=1)
                ),
            ],
        )
    )

    region_query = client.aggregation_query(query=user_query).count(
        alias="call_over_1_minute"
    )

    data = list(region_query.fetch())
    region_query_query_result = data[0][0] if len(data) == 1 else 0
    return region_query_query_result.value
