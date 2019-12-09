import os
import http.server
import socketserver
import io

import shutil
import subprocess

import json
import time

from threading import Thread

from cgi import parse_header, parse_multipart, FieldStorage

from musket_server import utils, tasks, tasks_factory, site
from musket_core import utils as musket_utils

class CustomHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)

        if "/favicon" in self.path:
            self.end_headers()

            return

        if "/site" in self.path:
            site.serve_get(self)

            return

        if "/gitclone" in self.path:
            self.end_headers()

            with self.server.task_manager.lock:
                params = utils.params(self.path)

                git_url = params["git_url"]

                destination = utils.temp_folder()

                if os.path.exists(destination):
                    shutil.rmtree(destination)

                os.mkdir(destination)

                subprocess.Popen(['git', 'clone', git_url, destination], stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

                project_id = params.pop("project_id", None)

                self.pickup_project(project_id)

                if "json" in params.keys():
                    id = json.dumps({"project_id": project_id})

                    self.wfile.write(id.encode())

            return

        if "/status" in self.path:
            self.end_headers()
            self.wfile.write("online".encode())

            return

        if "/project_fit" in self.path:
            self.end_headers()
            params = utils.params(self.path)

            id = tasks_factory.schedule_command_task(params["project"], params, self.server.task_manager)

            if "json" in params.keys():
                id = json.dumps({"task_id": id})

            self.wfile.write(id.encode())

            return

        if "/report" in self.path:
            self.end_headers()
            params = utils.params(self.path)

            task_id = params["task_id"]
            from_line = params["from_line"]

            dump = "dump" in params.keys()

            self.server.task_manager.update_tasks()

            report = utils.read_report(task_id, from_line, self.server.task_manager.task_status(task_id), dump).encode()

            self.wfile.write(report)

            return

        if "/last_report" in self.path:
            self.end_headers()
            params = utils.params(self.path)

            task_id = params["task_id"]

            self.server.task_manager.update_tasks()

            report = utils.read_report(task_id, -1000, self.server.task_manager.task_status(task_id)).encode()

            self.wfile.write(report)

            return

        if "/task_status" in self.path:
            self.end_headers()
            params = utils.params(self.path)

            task_id = params["task_id"]

            self.server.task_manager.update_tasks()

            result = str(self.server.task_manager.task_status(task_id)).encode()

            print("STATUS: " + result.decode())

            self.wfile.write(result)

            return

        if "/terminate" in self.path:
            self.end_headers()
            params = utils.params(self.path)

            task_id = params["task_id"]

            self.server.task_manager.terminate_task(task_id)

            self.wfile.write(json.dumps({"task_id": task_id}).encode("utf-8"))

            return

        if "/tasks_list" in self.path:
            self.end_headers()
            self.server.task_manager.update_tasks()

            with self.server.task_manager.lock:
                self.wfile.write(utils.tasks_info(self.server.task_manager).encode("utf-8"))

            return

        if "/project_list" in self.path:
            self.end_headers()
            self.server.task_manager.update_tasks()

            with self.server.task_manager.lock:
                self.wfile.write(utils.projects_info(self.server.task_manager).encode("utf-8"))

            return

        if "/all_state" in self.path:
            self.end_headers()
            self.server.task_manager.update_tasks()

            with self.server.task_manager.lock:
                self.wfile.write(utils.all_info(self.server.task_manager).encode("utf-8"))

            return

        if "/remove_project" in self.path:
            self.end_headers()
            self.server.task_manager.update_tasks()

            params = utils.params(self.path)

            project_id = params["project_id"]

            with self.server.task_manager.lock:
                shutil.rmtree(utils.project_path(project_id))

                self.wfile.write(json.dumps({"project_id": project_id}).encode("utf-8"))

            return

        if "/collect_delta" in self.path:
            self.end_headers()
            params = utils.params(self.path)

            id = tasks_factory.schedule_assembly_task(params["project"], params.pop("name", None), self.server.task_manager)

            if "dump" in params.keys():
                id = json.dumps({
                    "task_id": id
                })

            self.wfile.write(id.encode())

            return

        if "/download_delta" in self.path:
            params = utils.params(self.path)

            result_folder = utils.project_results_folder(params["project_id"])

            zip_path = os.path.join(result_folder, "project.zip")

            self.send_header('Content-type', 'application/zip')
            self.send_header("Content-Length", os.path.getsize(zip_path))
            self.end_headers()

            with self.server.task_manager.lock:
                with open(zip_path, "rb") as f:
                    chunk = f.read(1024)

                    while chunk:
                        self.wfile.write(chunk)

                        chunk = f.read(1024)

                shutil.rmtree(result_folder)

            return

        if "/remove_temp_folder":
            self.end_headers()

            with self.server.task_manager.lock:
                if os.path.exists(utils.temp_folder()):
                    shutil.rmtree(utils.temp_folder())

            return

    def do_POST(self):
        self.send_response(200)
        self.end_headers()

        if "/zipfile" in self.path:
            with self.server.task_manager.lock:
                destination = utils.temp_folder()

                shutil.rmtree(destination, True)
                musket_utils.ensure(destination)

                zip_path = utils.stream_to_zip(self.rfile, self.headers, "file", destination)

                shutil.unpack_archive(zip_path, destination)
                os.remove(zip_path)

                self.pickup_project()

    def pickup_project(self, name=None):
        print("picking: " + str(name))

        result = self.server.task_manager.workspace.pickup_project(name)

        result = "failure" if result == None else result

        shutil.rmtree(utils.temp_folder())

        self.wfile.write(result.encode())

def run_server(port, task_manager: tasks.TaskManager):
    if os.path.exists(utils.temp_folder()):
        shutil.rmtree(utils.temp_folder())

    with socketserver.TCPServer(("", port), CustomHandler) as httpd:
        httpd.task_manager = task_manager
        task_manager.server = httpd

        httpd.serve_forever()

def start_server(port, task_manager: tasks.TaskManager):
    task_manager.start()

    def target():
        run_server(port, task_manager)

    Thread(target=target).start()