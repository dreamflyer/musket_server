import os
import io

from cgi import parse_header, parse_multipart

from urllib.parse import parse_qs

from musket_core import utils

import shutil

REPORT_STATUS_NOT_AWAILABLE_YET = "report_not_awailable_yet"
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

def reports_folder():
    return os.path.expanduser("~/.musket_core/reports")

def read_report(task_id, from_line, task_status):
    path = os.path.join(reports_folder(), task_id, "report.log")

    result = ""

    if not task_status:
        return REPORT_STATUS_TASK_SCHEDULED

    if not os.path.exists(path) and task_status == "inprogress":
        return REPORT_STATUS_NOT_AWAILABLE_YET

    if task_status == "unknown_task":
        return REPORT_STATUS_TASK_UNKNOWN

    count = 0

    print("TASK STATUS: " + str(task_status))

    lines = []

    with open(path, "rb") as f:
        for line in io.TextIOWrapper(f):
            lines.append(line)

    print("from_line: " + str(from_line))

    lines = lines[int(from_line):]

    for line in lines:
        result += line

        count += 1

    return result if len(result) else "empty_string"

def listdir(path):
    items = os.listdir(path)

    return [item for item in items if not item.startswith('.')]

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
