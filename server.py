import os
import http.server
import socketserver

import shutil
import subprocess

from threading import Thread

from cgi import parse_header, parse_multipart, FieldStorage

from musket_server import utils, tasks, tasks_factory
from musket_core import utils as musket_utils

class CustomHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()

        if "gitclone" in self.path:
            destination = os.path.expanduser("~/.musket_core/temp")

            git_url = utils.git_url(self.path)

            destination = os.path.expanduser("~/.musket_core/temp")

            if os.path.exists(destination):
                shutil.rmtree(destination)

            os.mkdir(destination)

            subprocess.Popen(['git', 'clone', git_url, destination])

        if "project_fit" in self.path:
            params = utils.params(self.path)

            print(params)

            id = tasks_factory.schedule_command_task(params["project"], self.server.task_manager)

            self.wfile.write(id.encode())

        if "report" in self.path:
            params = utils.params(self.path)

            print(params)

            task_id = params["task_id"]
            from_line = params["from_line"]

            self.wfile.write(utils.read_report(task_id, from_line).encode())

    def do_POST(self):
        self.send_response(200)
        self.end_headers()

        if "zipfile" in self.path:
            with self.server.task_manager.lock:
                destination = utils.temp_folder()

                shutil.rmtree(destination, True)
                musket_utils.ensure(destination)

                zip_path = utils.stream_to_zip(self.rfile, self.headers, "file", destination)

                shutil.unpack_archive(zip_path, destination)
                os.remove(zip_path)

                self.pickup_project()

    def pickup_project(self):
        result = self.server.task_manager.workspace.pickup_project()

        result = "failure" if result == None else result

        shutil.rmtree(utils.temp_folder())

        self.wfile.write(result.encode())

def run_server(port, task_manager: tasks.TaskManager):
    with socketserver.TCPServer(("", port), CustomHandler) as httpd:
        httpd.task_manager = task_manager
        task_manager.server = http

        httpd.serve_forever()

def start_server(port, task_manager: tasks.TaskManager):
    task_manager.start()

    def target():
        run_server(port, task_manager)

    Thread(target=target).start()