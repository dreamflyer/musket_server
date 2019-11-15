import os

from musket_server import tasks, process_streamer, projects, utils

from musket_core import projects as musket_projects, utils as musket_utils

import asyncio

def schedule_command_task(project_id, task_manager: tasks.TaskManager):
    project = task_manager.workspace.project(project_id)

    task = ProjectFitTask(project)

    task_manager.schedule(task)

    return task.id

class ProjectFitTask(tasks.Task):
    def __init__(self, project: musket_projects.Project):
        tasks.Task.__init__(self)

        self.project = project

        musket_utils.ensure(self.report_dir())

    def cwd(self):
        return self.project.path

    def report_dir(self):
        return os.path.join(utils.reports_folder(), self.id)

    def do_task(self, data_handler):
        process_streamer.execute_command("musket fit", self.cwd(), data_handler)

    def on_data(self, data):
        with open(os.path.join(self.report_dir(), "report.log"), 'a+') as f:
            f.write(data)

    def on_complete(self):
        with open(os.path.join(self.report_dir(), "report.log"), 'a+') as f:
            f.write("\nreport_end")
