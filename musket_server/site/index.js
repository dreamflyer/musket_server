class Data {
    constructor() {
        this.tasks = [];
        this.projects = [];

        this.onUpdateHandlers = [];

        this.update();

        setInterval(() => this.update(), 1000);
    }

    update() {
        $.getJSON('../all_state', data => {
            this.tasks = (data && data["tasks"]) || [];
            this.projects = (data && data["projects"]) || [];

            this.onUpdateHandlers.forEach(handler => handler())
        });
    }

    onUpdate(handler) {
        this.onUpdateHandlers.push(handler);
    }
}

class MainView {
    constructor(data) {
        this.data = data;

        this.tasks = new Tasks();
        this.projects = new Projects();

        this.items = [this.tasks, this.projects];

        this.items.forEach(item => {
            item.onClick(()=> {
                this.hideAllTabs();

                item.show();
            });

            this.data.onUpdate(() => this.renderItem(item, this.data[item.data_id]));
        });
    }

    renderItem(item, data) {
        item.cleanup();

        item.render(data);
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

    render(data) {
        data.forEach(item => {
            this.container.appendChild(new ProjectItem(item).render());
        });
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
    }

    render() {
        let result = this.template;

        result = result.replace("#project_id#", this.data["project_id"]);
        result = result.replace("#project_id#", this.data["project_id"]);

        return renderHTML(result);
    }
}

function main() {
    let mainView = new MainView(new Data());
}
