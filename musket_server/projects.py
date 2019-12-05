import os

import shutil

from musket_core import projects, utils as musket_utils
from musket_server import tasks, utils

class ServerWorkspace:
    def __init__(self, task_manager):
        self.root = os.path.expanduser("~/.musket_core/server_workspace")

        self.task_manager: tasks.TaskManager = task_manager

        musket_utils.ensure(self.root)

    def project(self, id):
        return projects.Project(os.path.join(self.root, id))

    def list_projects(self):
        return [item for item in os.listdir(self.root) if os.path.isdir(os.path.join(self.root, item))]

    def exists(self, id):
        return id in self.list_projects()

    def pickup_project(self):
        temp_folder = utils.temp_folder()
        temp_content = [item for item in os.listdir(temp_folder) if os.path.isdir(os.path.join(temp_folder, item)) and not item.startswith("_")]

        if len(temp_content) > 0:
            project_id = temp_content[0]

            utils.copytree(os.path.join(temp_folder, project_id), os.path.join(self.root, project_id))

            return project_id

        return None