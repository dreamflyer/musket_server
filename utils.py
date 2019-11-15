import os
import io

from cgi import parse_header, parse_multipart

from urllib.parse import parse_qs

from musket_core import utils

import shutil

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

def read_report(task_id, from_line):
    path = os.path.join(reports_folder(), task_id, "report.log")

    result = ""

    if not os.path.exists(path):
        return result if len(result) else "empty_string"

    count = 0

    with open(path, "rb") as f:
        for line in io.TextIOWrapper(f):
            if count >= int(from_line):
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
