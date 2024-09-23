from google.cloud import firestore
from config import project_id
import os


def get_all_api_keys():
    client = firestore.Client(project=project_id, database="aireader")
    api_keys_ref = client.collection("ApiKeys")
    query = api_keys_ref.order_by("user_id")
    results = [doc.to_dict() for doc in query.stream()]
    print(results)
    return results


def save_api_keys_to_xlsx(api_keys):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["id", "name", "key"])
    for key in api_keys:
        ws.append([key["user_id"], key["name"], key["key"]])
    # save to current python directory
    current_directory = os.path.dirname(os.path.realpath(__file__))
    wb.save(os.path.join(current_directory, "api_keys.xlsx"))


if __name__ == "__main__":
    api_keys = get_all_api_keys()
    print(len(api_keys))
    save_api_keys_to_xlsx(api_keys)
