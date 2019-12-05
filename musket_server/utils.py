import os
import io

from cgi import parse_header, parse_multipart

from urllib.parse import parse_qs

from musket_core import utils

import shutil

import json

REPORT_STATUS_NOT_AVAILABLE_YET = "report_not_available_yet"
REPORT_STATUS_NO_UPDATES = "report_no_updates"
REPORT_STATUS_TASK_COMPLETE = "report_task_complete"
REPORT_STATUS_TASK_UNKNOWN = "report_task_unknown"
REPORT_STATUS_TASK_SCHEDULED = "report_task_scheduled"

def stream_to_zip(stream, headers, part_name, destination):
    ctype, pdict = parse_header(headers.get('Content-Type'))

    pdict['boundary'] = bytes(pdict['boundary'], "utf-8")

    content_len = int(headers.get('Content-length'))
    pdict['CONTENT-LENGTH'] = content_len

    postvars = parse_multipart(stream, pdict)

    in_path = os.path.join(destination, "file.zip")

    with open(in_path, "wb") as f:
        f.write(postvars["file"][0])

    return in_path

def git_url(request_path):
    parsed_path = parse_qs(request_path);

    key = list(parsed_path.keys())[0]

    return parsed_path[key][0]

def params(request_path):
    result = {}

    parsed_path = parse_qs(request_path[request_path.index('?') + 1:])

    for item in list(parsed_path.keys()):
        result[item] = parsed_path[item][0]

    return result

def temp_folder():
    return os.path.expanduser("~/.musket_core/temp")

def workspace_folder():
    return os.path.expanduser("~/.musket_core/server_workspace")

def project_path(project_id):
    return os.path.join(workspace_folder(), project_id)

def reports_folder():
    return os.path.expanduser("~/.musket_core/reports")

def read_report(task_id, from_line, task_status, dump=False):
    path = os.path.join(reports_folder(), task_id, "report.log")

    result = ""

    not_ready = False

    if not task_status:
        result = REPORT_STATUS_TASK_SCHEDULED

        not_ready = True

    if not os.path.exists(path) and task_status == "inprogress":
        result = REPORT_STATUS_NOT_AVAILABLE_YET

        not_ready = True

    if task_status == "unknown_task":
        result = REPORT_STATUS_TASK_UNKNOWN

        not_ready = True

    if not_ready:
        if dump:
            return json.dumps({
                "text": result,
                "next": -1000
            })

        return result

    count = 0

    lines = []

    with open(path, "rb") as f:
        for line in io.TextIOWrapper(f):
            lines.append(line)

    size = len(lines)

    lines = lines[int(from_line):]

    for line in lines:
        #print("LINE: (" + line + ")")

        result += line.strip() + "\r\n"

        count += 1

    if dump:
        return json.dumps({
            "text": result if len(result) else "empty_string",
            "next": size
        })

    return result if len(result) else "empty_string"

def listdir(path):
    items = os.listdir(path)

    return [item for item in items if not item.startswith('.')]

def project_ids():
    return [item for item in os.listdir(workspace_folder()) if not item.startswith(".")]

def associated_tasks(tasks_manager, project_id):
    result = []

    for item in tasks_manager.tasks:
        info = item.info()

        if "project_id" in info.keys() and info["project_id"] == project_id:
            result.append(info)

    return result

def projects_info(tasks_manager, dump=True):
    ids = project_ids()

    result = []

    for item in ids:
        project_info = {
            "project_id": item,

            "tasks": associated_tasks(tasks_manager, item)
        }

        result.append(project_info)

    return json.dumps(result) if dump else result

def tasks_info(tasks_manager, dump=True):
    result = []

    for item in tasks_manager.tasks:
        result.append(item.info())

    return json.dumps(result) if dump else result

def all_info(tasks_manager, dump=True):
    result = {
        "tasks": tasks_info(tasks_manager, False),
        "projects": projects_info(tasks_manager, False)
    }

    return json.dumps(result) if dump else result

def project_results(project_id):
    experiments_path = os.path.join(project_path(project_id), "experiments")

    experiments = listdir(experiments_path)

    all_items = []

    for item in experiments:
        experiment_path = os.path.join(experiments_path, item)

        get_experiment_items(experiment_path, all_items)

        return [os.path.relpath(item, workspace_folder()) for item in all_items]

def results_zip():
    return os.path.join(temp_folder(), "project.zip")

def collect_results(project_id):
    workspace_dir = workspace_folder()
    files = project_results(project_id)

    temp = temp_folder()

    temp = os.path.join(temp_folder(), "zip")

    if os.path.exists(temp):
        return "busy"

    utils.ensure(temp)

    for item in files:
        src = os.path.join(workspace_dir, item)

        if not os.path.exists(src):
            continue

        dst = os.path.join(temp, item)

        parent = os.path.dirname(dst)

        if not os.path.exists(parent):
            utils.ensure(parent)

        shutil.copy(src, dst)

    utils.archive(os.path.join(temp, project_id), os.path.join(temp_folder(), "project"))

def get_experiment_items(src, all_items):
    all_items.append(os.path.join(src, "summary.yaml"))

    list_all(os.path.join(src, "weights"), all_items)
    list_all(os.path.join(src, "examples"), all_items)
    list_all(os.path.join(src, "metrics"), all_items)

def list_all(src, all_items):
    if not os.path.exists(src):
        return

    items = [item for item in os.listdir(src) if not item.startswith('.')]

    for item in items:
        full_path = os.path.join(src, item)

        if os.path.isdir(full_path):
            list_all(full_path, all_items)
        else:
            all_items.append(full_path)

def copytree(src, dst):
    utils.ensure(dst)

    for item in listdir(src):
        src_item = os.path.join(src, item)
        dst_item = os.path.join(dst, item)

        if os.path.isdir(src_item):
            copytree(src_item, dst_item)
        else:
            if os.path.exists(dst_item):
                os.remove(dst_item)

            shutil.copy(src_item, dst_item)