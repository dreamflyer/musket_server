class Data {
    constructor() {
        this.tasks = [];
        this.projects = [];

        this.onUpdateHandlers = [];

        this.projectUnlockers = [];

        this.update();
    }

    update() {
        getJSON('../all_state').then(data => {
            let projects = (data && data["projects"]) || [];

            this.applyProjects(projects);

            this.onUpdateHandlers.forEach(handler => handler());

            return true
        }).then(result => setTimeout(() => this.update(), 1000));
    }

    applyProjects(projects) {
        let newTasks = [];
        let newProjects = [];

        this.projectUnlockers.forEach(item => {
            if(item.canUnlock(projects)) {
                item.unlock();

                item.unlocked = true;
            }
        });

        this.projectUnlockers = this.projectUnlockers.filter(item => !item.unlocked);

        projects.forEach(item => {
            let old_item = this.getProject(item["project_id"], this.projects);

            if(!old_item) {
                item.update = "create";

                newProjects.push(item);

                return;
            }

            if(old_item.update === "lock" || this.isProjectsEqual(old_item, item)) {
                newProjects.push(old_item);

                return;
            }

            item.update = "update";

            newProjects.push(item);
        });

        this.projects.forEach(item => {
            let new_item = this.getProject(item["project_id"], projects);

            if(!new_item) {
                if(item.update === "lock") {
                    newProjects.push(item);

                    return;
                }

                item.update = "delete";

                newProjects.push(item);
            }
        });

        this.tasks = newTasks;
        this.projects = newProjects;
    }

    isProjectsEqual(project1, project2) {
        if(project1["project_id"] !== project2["project_id"]) {
            return false;
        }

        if(!this.isTasksEqual(project1["tasks"], project2["tasks"])) {
            return false;
        }

        return true;
    }

    isTasksEqual(tasks1, tasks2) {
        return isArraysEqual(tasks1, tasks2, (item1, item2)=> this.isTaskEqual(item1, item2));
    }

    isTaskEqual(t1, t2) {
        if(!t1 || !t2) {
            return t1 == t2;
        }

        let task1 = t1;
        let task2 = t2;

        if(task1["task_id"] !== task2["task_id"]) {
            return false;
        }

        if(task1["status"] !== task2["status"]) {
            return false;
        }

        return true;
    }

    onUpdate(handler) {
        this.onUpdateHandlers.push(handler);
    }

    getProject(project_id, projects) {
        return projects.find(item => item["project_id"] === project_id);
    }

    unlockProject(project_id) {
        let project = this.getProject(project_id, this.projects);

        if(project) {
            project.update = "update";
        }
    }

    lockProject(project_id) {
        let project = this.getProject(project_id, this.projects);

        if(project) {
            project.update = "lock";
        }
    }

    deleteProject(project_id) {
        this.lockProject(project_id);

        getJSON('../remove_project?project_id=' + project_id).then(data => {
            this.unlockProject(data["project_id"]);
        });
    }

    terminateTask(project) {
        if(!project.activeTask) {
            return
        }

        this.lockProject(project.id);

        getJSON('../terminate?task_id=' + project.activeTask).then(data => {
            this.unlockProject(project.id);
        });
    }

    runProject(project) {
        let project_id = project.id;

        this.lockProject(project_id);

        getJSON('../project_fit?project=' + project_id + "&json=true").then(data => {
            this.projectUnlockers.push({
                canUnlock: (newProjects) => {
                    let project = this.getProject(project_id, newProjects);

                    return (project && project.tasks && project.tasks.find((item) => item["task_id"] == data["task_id"])) ? true : false;
                },

                unlock: () => this.unlockProject(project_id),

                unlocked: false
            });
        });
    }
}

class TerminalView {
    constructor() {
        this.terminal = new Terminal();

        this.terminal.convertEol = true;

        this.terminal.open(document.getElementById('terminal'));
    }

    start(taskId) {
        this.stop();

        this.handler = {
            report: (data) => {
                this.terminal.write(data);
            },

            stop: false
        };

        readReport(taskId, -1000, this.handler);
    }

    stop() {
        if(this.handler) {
            this.handler.stop = true;

            this.handler = null;
        }

        this.terminal.clear();
    }
}

class MainView {
    constructor(data) {
        this.data = data;

        this.projects = new Projects();

        this.items = [this.projects];

        this.terminalView = new TerminalView();

        this.items.forEach(item => {
            item.onEvent("Delete", (dataId, project) => {
                data.deleteProject(project.id);
            });

            item.onEvent("Run", (dataId, project) => {
                data.runProject(project);
            });

            item.onEvent("Stop", (dataId, project) => {
                data.terminateTask(project);
            });

            item.onEvent("Report", (dataId, project) => {
                this.terminalView.start(project.activeTask);
            });

            item.onClick(()=> {
                this.hideAllTabs();

                item.show();
            });

            this.data.onUpdate(() => this.applyData(item, this.data[item.data_id]));
        });
    }

    applyData(item, data) {
        item.applyData(data);
    }
}

class Projects {
    constructor() {
        this.container = document.getElementById("tab-projects-content");
        this.onClickHandler = null;
        this.data_id = "projects";
        this.children = []

        this.eventHandlers = {}
    }

    onEvent(name, handler) {
        this.eventHandlers[name] = handler;
    }

    cleanup() {
        this.container.innerHTML = "";
    }

    onClick(handler) {
        this.onClickHandler = handler;
    }

    applyData(data) {
        data.forEach(item => {
            let found = this.children.find(child => child.id === item["project_id"]);

            if(!found) {
                let projectItem = new ProjectItem(item);

                this.container.appendChild(projectItem.render());
                this.children.push(projectItem);

                projectItem.onDestroy(() => {
                    this.children = this.children.filter(toRemove => toRemove !== projectItem);
                });

                projectItem.onClick((name) => {
                   let handler = this.eventHandlers[name];

                   if(handler) {
                       handler(this.data_id, projectItem);
                   }
                });

                found = projectItem;
            }

            found.applyData(item);
        })
    }
}

class ProjectItem {
    constructor(data) {
        this.data = data;

        this.container = document.getElementById("tab-projects-content");
        this.template = document.getElementById("project-item-template").innerHTML;

        this.onDestroyHandlers = [];
        this.onClickHandlers = [];

        this.activeTask = null;
    }

    get id() {
        return this.data["project_id"];
    }

    render() {
        if(!this.element) {
            let result = this.template;

            result = result.replace("#project_id#", this.data["project_id"]);

            this.element = renderHTML(result);

            this.getButton("Run").wrapper = this;
            this.getButton("Stop").wrapper = this;
            this.getButton("Delete").wrapper = this;

            this.getItem("a", "Report").wrapper = this;
        }

        return this.element;
    }

    applyData(data) {
        this.data = data;

        if(this.data.update === "lock") {
            this.setButtonState("Run", "btn-secondary", "skip");
            this.setButtonState("Stop", "btn-secondary", "skip");
            this.setButtonState("Delete", "btn-secondary", "skip");

            return
        }

        this.activeTask = this.getActiveTask(data) && this.getActiveTask(data)["task_id"];

        if(this.data.update === "create" || this.data.update === "update") {
            if(this.isInProgress(data) || this.isSheduled(data)) {
                this.setButtonState("Run", "btn-success", false);
                this.setButtonState("Stop", "btn-danger", true);
                this.setButtonState("Delete", "btn-secondary", true);
            } else {
                this.setButtonState("Run", "btn-success", true);
                this.setButtonState("Stop", "btn-danger", false);
                this.setButtonState("Delete", "btn-danger", true);
            }

            this.data.update = null;

            return
        }

        if(this.data.update === "delete") {
            this.destroy();
        }
    }

    getActiveTask(project) {
        if(!project.tasks) {
            return null;
        }

        return project.tasks.find((item) => item.status === "inprogress")
    }

    isInProgress(project) {
        return this.getActiveTask(project) ? true : false;
    }

    isSheduled(project) {
        if(!project.tasks) {
            return false;
        }

        if(project.tasks.length === 0) {
            return false;
        }

        return project.tasks.find((item) => !item.status) ? true : false;
    }

    destroy() {
        if(this.element) {
            this.element.remove();
        }

        this.onDestroyHandlers.forEach(item => item());

        this.onClickHandlers = [];
        this.onDestroyHandlers = [];
    }

    onDestroy(handler) {
        this.onDestroyHandlers.push(handler);
    }

    getButton(name) {
        return this.getItem("button", name);
    }

    getItem(tag, label) {
        let buttons = this.element.getElementsByTagName(tag);

        for(let i = 0; i < buttons.length; i++) {
            if(buttons.item(i).innerText === label) {
                return buttons.item(i);
            }
        }
    }

    setClass(buttonName, type) {
        let button = this.getButton(buttonName);

        button.classList.remove("btn-danger");
        button.classList.remove("btn-success");
        button.classList.remove("btn-secondary");

        button.classList.add(type);
    }

    setButtonState(name, type, visibility) {
        let button = this.getButton(name);

        this.setClass(name, type);

        if(visibility === "skip") {
            return
        }

        button.style.display = visibility ? null : "none";
    }

    click(name) {
        this.onClickHandlers.forEach(item => item(name));

        this.applyData(this.data);
    }

    onClick(handler) {
        this.onClickHandlers.push(handler);
    }
}

function main() {
    Dropzone.autoDiscover = false;

    let dropzone = new Dropzone("div#upload-zip", {
        url: "/zipfile",
        dictDefaultMessage: "drop ZIP file here",
        complete: function() {
            this.removeAllFiles(true);
        }
    });

    let mainView = new MainView(new Data());
}
