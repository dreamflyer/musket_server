import os

from musket_server import tasks, process_streamer, projects, utils

from musket_core import projects as musket_projects, utils as musket_utils

import asyncio

import time

import tqdm

def schedule_command_task(project_id, params, task_manager: tasks.TaskManager):
    project = task_manager.workspace.project(project_id)

    task = ProjectFitTask(project, params)

    task_manager.schedule(task)

    return task.id

def schedule_assembly_task(project_id, experiment, task_manager: tasks.TaskManager):
    project = task_manager.workspace.project(project_id)

    task = DeltaAssemblyTask(project, experiment)

    task_manager.schedule(task)

    return task.id

class DeltaAssemblyTask(tasks.Task):
    def __init__(self, project: musket_projects.Project, experiment=None):
        tasks.Task.__init__(self)

        self.project = project
        self.process = None
        self.experiment = experiment

        musket_utils.ensure(self.report_dir())

    def cwd(self):
        return os.path.dirname(__file__)

    def report_dir(self):
        return os.path.join(utils.reports_folder(), self.id)

    def do_task(self, data_handler):
        cmd = "python collect_results.py " + os.path.basename(self.project.path)

        if self.experiment:
            cmd = cmd + " " + self.experiment

        process_streamer.execute_command(cmd, self.cwd(), data_handler, self.set_process, True)

    def on_data(self, data):
        with open(os.path.join(self.report_dir(), "report.log"), 'a+') as f:
            f.write(data)

    def on_complete(self):
        print("TASK STOP")

    def set_process(self, process):
        self.process = process

    def terminate(self):
        if self.process:
            self.process.terminated = True

            self.process.kill()

    def info(self):
        return {
            "assembly": os.path.basename(self.project.path),
            "project_id": os.path.basename(self.project.path),
            "task_id": self.id,
            "status": self.status,
            "type": "project_result_assembly"
        }

class ProjectFitTask(tasks.Task):
    def __init__(self, project: musket_projects.Project, params):
        tasks.Task.__init__(self)

        self.project = project
        self.process = None
        self.params = params

        musket_utils.ensure(self.report_dir())

    def cwd(self):
        return self.project.path

    def report_dir(self):
        return os.path.join(utils.reports_folder(), self.id)

    def do_task(self, data_handler):
        process_streamer.execute_command("musket fit" + self.serializeParams(), self.cwd(), data_handler, self.set_process)

    def on_data(self, data):
        with open(os.path.join(self.report_dir(), "report.log"), 'a+') as f:
            f.write(data)

    def on_complete(self):
        print("TASK STOP")

    def set_process(self, process):
        self.process = process

    def terminate(self):
        if self.process:
            self.process.terminated = True

            self.process.kill()

    def info(self):
        return {
            "project_id": os.path.basename(self.project.path),
            "task_id": self.id,
            "status": self.status,
            "type": "project_fit"
        }

    def serializeParams(self):
        result = ''

        for item in self.params.keys():
            if item == "project":
                continue

            if item == "json":
                continue

            result += " --" + item + " " + self.params[item]

        return result

class FakeTask(tasks.Task):
    def __init__(self, project: musket_projects.Project):
        tasks.Task.__init__(self)

        self.project = project
        self.process = None

        musket_utils.ensure(self.report_dir())

    def cwd(self):
        return self.project.path

    def report_dir(self):
        return os.path.join(utils.reports_folder(), self.id)

    def do_task(self, data_handler):
        process_streamer.execute_command("python /Users/dreamflyer/Desktop/musket_server/fake_task.py", self.cwd(), data_handler, self.set_process)

    def on_data(self, data):
        with open(os.path.join(self.report_dir(), "report.log"), 'a+') as f:
            f.write(data)

    def on_complete(self):
        print("TASK STOP")

    def set_process(self, process):
        self.process = process

    def terminate(self):
        if self.process:
            self.process.terminated = True

            self.process.kill()

    def info(self):
        return {
            "project_id": os.path.basename(self.project.path),
            "task_id": self.id,
            "status": self.status,
            "type": "project_fit"
        }