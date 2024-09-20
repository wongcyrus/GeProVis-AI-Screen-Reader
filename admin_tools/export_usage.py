import datetime
from google.cloud import firestore
from config import project_id
import os

def get_all_usages():
    client = firestore.Client(project=project_id, database="aireader")
    usages_ref = client.collection("Usage")
    query = usages_ref.order_by("time")
    results = [doc.to_dict() for doc in query.stream()]

    return results

def get_usages_by_user_id():
    client = firestore.Client(project=project_id, database="aireader")
    usages_ref = client.collection("Usage")

    query = usages_ref.where("user_id", "==", str(100)).where(
        "time", ">", datetime.datetime.now() - datetime.timedelta(days=1)
    )

    total_cost = 0
    for doc in query.stream():
        total_cost += doc.to_dict().get("cost", 0)

    print(total_cost)
    return total_cost

def get_usages_by_region():
    client = firestore.Client(project=project_id, database="aireader")
    usages_ref = client.collection("Usage")

    query = usages_ref.where("model_region", "==", "europe-west3").where(
        "time", ">", datetime.datetime.now() - datetime.timedelta(days=1)
    )

    count = sum(1 for _ in query.stream())

    print(count)
    return count

def save_usages_to_xlsx(usages):
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(["id", "cost", "time"])
    for usage in usages:
        time = usage["time"].replace(tzinfo=None) if usage["time"] else None
        ws.append([usage["user_id"], usage["cost"], time])
    # save to current python directory
    current_directory = os.path.dirname(os.path.realpath(__file__))
    wb.save(os.path.join(current_directory, "usage.xlsx"))



if __name__ == "__main__":
    # usages = get_all_usages()
    # print(len(usages))
    # save_usages_to_xlsx(usages)
    get_usages_by_region()
