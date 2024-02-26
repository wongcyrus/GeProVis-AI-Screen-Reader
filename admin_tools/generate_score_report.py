from google.cloud import datastore
from google.cloud.datastore.query import PropertyFilter
from config import project_id
import os
from openpyxl import Workbook

def get_all_api_keys():
    client = datastore.Client(project=project_id)
    query = client.query(kind="ApiKey")
    query.order = ["user_id"]
    results = list(query.fetch())
    
    return results

def completed_task(user_id: str) -> list:
    client = datastore.Client("pytest-runner1")
    query = client.query(kind="CompletedTask")
    query.add_filter(filter=PropertyFilter(        
        property_name="user_id",
        operator="=",
        value=user_id))
    results = query.fetch()
    results = list(map(lambda x: x["question"], results))
    results.sort()
    return list(results)

def save_to_xlsx(student_task:dict, all_tasks:list):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    header = ["id","score"]
    # remove the first 4 characters "task" from all_tasks
    header.extend(list(map(lambda x: x[4:], all_tasks)))
    ws.append(header)

    #Loop through student_task with for loop sort by key
    for key, value in sorted(student_task.items(), key=lambda item: str(item[0])):
        row = [key,len(value)]
        for task in all_tasks:
            if task in value:
                row.append("1")
            else:
                row.append("0")
        ws.append(row)
    current_directory = os.path.dirname(os.path.realpath(__file__))
    wb.save(os.path.join(current_directory, "scores.xlsx"))  


if __name__ == "__main__":
    api_keys = get_all_api_keys()
    # api_keys = api_keys[:10]
    
    # extract user_id from api_keys
    print("Get User Records.")
    user_ids = list(map(lambda x: {"id":x["user_id"],"tasks":completed_task(x["user_id"])}, api_keys))
    # Combine list of dict into one dict
    student_task = {d['id']: d['tasks'] for d in user_ids} 
    # Join all tasks into a set
    all_tasks = set().union(*student_task.values())
    # convert all_tasks to list and sort it 
    all_tasks = list(all_tasks)
    all_tasks.sort()
    print("Save to xlsx.")
    save_to_xlsx(student_task,all_tasks)    
    print("Done.")
    