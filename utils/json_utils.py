import json
import os

THREADS_FILE = "threads.json"
if not os.path.exists(THREADS_FILE):
    with open(THREADS_FILE, 'w') as f:
        json.dump({}, f, indent=4)

def write_to_json(thread_id, data):
    with open(THREADS_FILE, 'r') as f:
        file_data = json.load(f)

    if thread_id not in file_data:
        file_data[thread_id] = []

    file_data[thread_id].append(data)

    with open(THREADS_FILE, 'w') as f:
        json.dump(file_data, f, indent=4)

def update_run_steps(thread_id, run_id, serialized_run_steps, status):
    with open(THREADS_FILE, 'r') as f:
        file_data = json.load(f)

    if thread_id in file_data:
        for entry in file_data[thread_id]:
            if entry["server"]["run_id"] == run_id:
                if status == "completed":
                    serialized_run_steps.reverse()
                    seen_file_ids = set()
                    unique_steps = []
                    for step in serialized_run_steps:
                        new_steps = []
                        for s in step["steps"]:
                            if s["type"] == "image":
                                if s["content"] not in seen_file_ids:
                                    new_steps.append(s)
                                    seen_file_ids.add(s["content"])
                            else:
                                new_steps.append(s)
                        if new_steps:
                            step["steps"] = new_steps
                            unique_steps.append(step)

                    entry["server"]["run_steps"] = unique_steps
                    entry["server"]["status"] = status
                else:
                    entry["server"]["run_steps"] = []
                    entry["server"]["status"] = "in_progress"
                break

    with open(THREADS_FILE, 'w') as f:
        json.dump(file_data, f, indent=4)
