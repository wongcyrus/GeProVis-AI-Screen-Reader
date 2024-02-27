from google.cloud import datastore
from config import project_id
import os


def get_all_usages():
    client = datastore.Client(project=project_id)
    query = client.query(kind="Usage")
    query.order = ["time"]
    results = list(query.fetch())

    return results


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
    usages = get_all_usages()
    print(len(usages))
    save_usages_to_xlsx(usages)
