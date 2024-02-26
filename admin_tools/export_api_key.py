from google.cloud import datastore
from config import project_id
import os

def get_all_api_keys():
    client = datastore.Client(project=project_id)
    query = client.query(kind="ApiKey")
    query.order = ["user_id"]
    results = list(query.fetch())
    
    return results

def save_api_keys_to_xlsx(api_keys):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["id","name","key"])
    for key in api_keys:
        ws.append([key["user_id"],key["name"],key.key.name])
    # save to current python directory
    current_directory = os.path.dirname(os.path.realpath(__file__))
    wb.save(os.path.join(current_directory, "api_keys.xlsx"))  


if __name__ == "__main__":
    api_keys = get_all_api_keys()
    print(len(api_keys))
    save_api_keys_to_xlsx(api_keys)