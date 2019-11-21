import time

import uuid

from threading import Lock, Thread
from async_promises import Promise

from musket_server import projects

TASK_STATUS_INPROGRESS = "inprogress"
TASK_STATUS_COMPLETE = "complete"
TASK_STATUS_UNKNOWN = "unknown_task"

class Task:
    def __init__(self):
        self.id = str(uuid.uuid4())

        self.status = None
        self.manager = None

    def register(self, manager):
        self.manager = manager

    def complete(self):
        with self.manager.lock:
            self.on_complete()

            self.manager.complete_task(self)

    def run(self):
        print("running")

        def rejection(cause):
            print(cause)

        Promise(lambda resolve, reject: resolve(self.do_task(self.on_data) or True)).then(lambda success: (self.complete() or True), rejection)

    def on_data(self, data):
        pass

    def on_complete(self):
        pass

    def do_task(self, data_handler):
        pass

class TaskManager:
    def __init__(self, max_tasks):
        self.tasks = []
        self.max_tasks = max_tasks
        self.lock = Lock()
        self.running = True
        self.server = None
        self.workspace = projects.ServerWorkspace(self)

    def schedule(self, task):
        task.register(self)

        self.tasks.append(task)

    def complete_task(self, task):
        task.status = TASK_STATUS_COMPLETE

    def task_status(self, task_id):
        with self.lock:
            for item in self.tasks:
                if item.id == task_id:
                    return item.status

        return TASK_STATUS_UNKNOWN

    def update_tasks(self):
        with self.lock:
            for item in self.tasks:
                active_tasks = self.active_tasks_num()

                if active_tasks >= self.max_tasks:
                    break

                if not item.status:
                    item.status = TASK_STATUS_INPROGRESS
                    item.run()

    def active_tasks_num(self):
        return len([item for item in self.tasks if item.status == TASK_STATUS_INPROGRESS])

    def shutdown(self):
        self.server.shutdown()
        self.server.server_close()

    def loop(self):
        try:
            while self.running:
                self.update_tasks()

                time.sleep(1)
        finally:
            self.shutdown()

    def start(self):
        Thread(target=self.loop).start()
