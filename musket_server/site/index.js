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

            if(old_item.update === "lock" || this.is_projects_equal(old_item, item)) {
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

    is_projects_equal(project1, project2) {
        if(project1["project_id"] !== project2["project_id"]) {
            return false;
        }

        if(!this.is_tasks_equal(project1["task"], project2["task"])) {
            return false;
        }

        return true;
    }

    is_tasks_equal(t1, t2) {
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

    runProject(project_id) {
        this.lockProject(project_id);

        getJSON('../project_fit?project=' + project_id + "&json=true").then(data => {
            this.projectUnlockers.push({
                canUnlock: (newProjects) => {
                    let project = this.getProject(project_id, newProjects);

                    return (project && project.task && project.task["task_id"] === data["task_id"]) ? true : false;
                },

                unlock: () => this.unlockProject(project_id),

                unlocked: false
            });
        });
    }
}

class MainView {
    constructor(data) {
        this.data = data;

        this.tasks = new Tasks();
        this.projects = new Projects();

        this.items = [this.tasks, this.projects];

        this.items.forEach(item => {
            item.onEvent("Delete", (dataId, eventId) => {
                data.deleteProject(eventId);
            });

            item.onEvent("Run", (dataId, eventId) => {
                data.runProject(eventId);
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

    hideAllTabs() {
        this.tasks.hide();
        this.projects.hide();
    }
}

class Projects {
    constructor() {
        this.tab = document.getElementById("tab-projects");
        this.container = document.getElementById("tab-projects-content");
        this.onClickHandler = null;
        this.data_id = "projects";

        this.tab.wrapper = this;

        this.children = []

        this.eventHandlers = {}
    }

    onEvent(name, handler) {
        this.eventHandlers[name] = handler;
    }

    cleanup() {
        this.container.innerHTML = "";
    }

    hide() {
        this.container.style.display = "none";
        this.tab.classList.remove("active");
    }

    show() {
        this.container.style.display = null;
        this.tab.classList.add("active");
    }

    tabClick() {
        if(!this.onClickHandler){
            return
        }

        this.onClickHandler();
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
                       handler(this.data_id, projectItem.id);
                   }
                });

                found = projectItem;
            }

            found.applyData(item);
        })
    }
}

class Tasks {
    constructor() {
        this.tab = document.getElementById("tab-tasks");
        this.container = document.getElementById("tab-tasks-content");
        this.onClickHandler = null;
        this.data_id = "tasks";

        this.tab.wrapper = this;
    }

    onEvent(name, handler) {

    }

    cleanup() {
        //this.container.innerHTML = "";
    }

    hide() {
        this.container.style.display = "none";
        this.tab.classList.remove("active");
    }

    show() {
        this.container.style.display = null;
        this.tab.classList.add("active");
    }

    tabClick() {
        if(!this.onClickHandler){
            return
        }

        this.onClickHandler();
    }

    applyData(data) {

    }

    onClick(handler) {
        this.onClickHandler = handler;
    }

    render(data) {

    }
}

class ProjectItem {
    constructor(data) {
        this.data = data;

        this.container = document.getElementById("tab-projects-content");
        this.template = document.getElementById("project-item-template").innerHTML;

        this.onDestroyHandlers = [];
        this.onClickHandlers = [];
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

        if(this.data.update === "create" || this.data.update === "update") {
            let status = this.data.task && this.data.task.status;

            if(status === "inprogress") {
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
        let buttons = this.element.getElementsByTagName("button");

        for(let i = 0; i < buttons.length; i++) {
            if(buttons.item(i).innerText === name) {
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
    let mainView = new MainView(new Data());
}
