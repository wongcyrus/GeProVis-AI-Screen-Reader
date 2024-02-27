import datetime
from google.cloud import datastore
from config import project_id
from google.cloud.datastore.query import BaseCompositeFilter, PropertyFilter
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


def get_usages_by_user_id():
    client = datastore.Client(project=project_id)
    user_query = client.query(kind="Usage")

    user_query.add_filter(
        filter=BaseCompositeFilter(
            "AND",
            [
                PropertyFilter("user_id", "=", str(100)),
                PropertyFilter(
                    "time", ">", datetime.datetime.now() - datetime.timedelta(days=1)
                ),
            ],
        )
    )

    user_cost_query = client.aggregation_query(query=user_query).sum(
        property_ref="cost", alias="total_cost_over_1_day"
    )

    data  = list(user_cost_query.fetch())
    user_cost_query_result = data[0][0] if len(data) == 1 else 0
    print(user_cost_query_result.value)
    # for aggregation_results in user_cost_query_result:
    #     for aggregation_result in aggregation_results:
    #         if aggregation_result.alias == "total_cost_over_1_day":
    #             print(
    #                 f"Total sum of hours in completed tasks is {aggregation_result.value}"
    #             )
    # print(results)
    # return results


if __name__ == "__main__":
    # usages = get_all_usages()
    # print(len(usages))
    # save_usages_to_xlsx(usages)
    get_usages_by_user_id()
