import os
import http.server
import socketserver
import io

import shutil
import subprocess

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

        if "/gitclone" in self.path:
            self.end_headers()
            with self.server.task_manager.lock:
                git_url = utils.git_url(self.path)

                destination = utils.temp_folder()

                if os.path.exists(destination):
                    shutil.rmtree(destination)

                os.mkdir(destination)

                subprocess.Popen(['git', 'clone', git_url, destination])

                self.pickup_project()

        if "/status" in self.path:
            self.end_headers()
            self.wfile.write("online".encode())

        if "/project_fit" in self.path:
            self.end_headers()
            params = utils.params(self.path)

            id = tasks_factory.schedule_command_task(params["project"], self.server.task_manager)

            self.wfile.write(id.encode())

        if "/report" in self.path:
            self.end_headers()
            params = utils.params(self.path)

            task_id = params["task_id"]
            from_line = params["from_line"]

            self.server.task_manager.update_tasks()

            report = utils.read_report(task_id, from_line, self.server.task_manager.task_status(task_id)).encode()

            self.wfile.write(report)

        if "/last_report" in self.path:
            self.end_headers()
            params = utils.params(self.path)

            task_id = params["task_id"]

            self.server.task_manager.update_tasks()

            report = utils.read_report(task_id, -1000, self.server.task_manager.task_status(task_id)).encode()

            self.wfile.write(report)

        if "/task_status" in self.path:
            self.end_headers()
            params = utils.params(self.path)

            task_id = params["task_id"]

            self.server.task_manager.update_tasks()

            result = str(self.server.task_manager.task_status(task_id)).encode()

            print("STATUS: " + result.decode())

            self.wfile.write(result)

        if "/terminate" in self.path:
            self.end_headers()
            params = utils.params(self.path)

            task_id = params["task_id"]

            self.server.task_manager.terminate_task(task_id)

        if "/tasks_list" in self.path:
            self.end_headers()
            self.server.task_manager.update_tasks()

            with self.server.task_manager.lock:
                self.wfile.write(utils.tasks_info(self.server.task_manager).encode("utf-8"))

        if "/project_list" in self.path:
            self.end_headers()
            self.server.task_manager.update_tasks()

            with self.server.task_manager.lock:
                self.wfile.write(utils.projects_info(self.server.task_manager).encode("utf-8"))

        if "/collect_delta" in self.path:
            self.end_headers()
            params = utils.params(self.path)

            id = tasks_factory.schedule_assembly_task(params["project"], self.server.task_manager)

            self.wfile.write(id.encode())

        if "/download_delta" in self.path:
            zip_path = os.path.join(utils.temp_folder(), "project.zip")

            self.send_header('Content-type', 'application/zip')
            self.send_header("Content-Length", os.path.getsize(zip_path))
            self.end_headers()

            with self.server.task_manager.lock:
                with open(zip_path, "rb") as f:
                    chunk = f.read(1024)

                    while chunk:
                        self.wfile.write(chunk)

                        chunk = f.read(1024)

                shutil.rmtree(utils.temp_folder())

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