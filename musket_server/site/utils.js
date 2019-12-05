function renderHTML(htmlString) {
    let div = document.createElement('div');

    div.innerHTML = htmlString.trim();

    return div.firstChild;
}

function getJSON(url) {
    return new Promise(resolve => {
        $.getJSON(url, data => resolve(data));
    });
}

function isArraysEqual(list1, list2, comparator) {
    if(!list1 || !list2) {
        return list1 == list2;
    }

    if(list1.length !== list2.length) {
        return false;
    }

    let length = list1.length;

    for(let i = 0; i < length; i++) {
        let current = list1[i];

        if(!list2.find((item) => comparator(current, item))) {
            return false;
        }
    }

    return true;
}

function readReport(task_id, from_line, handler) {
    if(handler.stop) {
        return;
    }

    getJSON("../reports?task_id=" + task_id + "&from_line=" + from_line + "&dump=true").then((data) => {
        if(handler.stop) {
            return;
        }

        let text = data.text;

        if(text === "empty_string") {
            setTimeout(() => readReport(task_id, from_line, handler), 1000);

            return;
        }

        if(text.indexOf("report_task_scheduled") >= 0) {
            handler.report("task will be perform later...\r\n");

            return;
        }

        if(text.indexOf("report_task_unknown") >= 0) {
            handler.report("no active tasks found.\r\n");

            return;
        }

        if(text.indexOf("report_not_available_yet") >= 0) {
            handler.report("awaiting report...\r\n");

            setTimeout(() => readReport(task_id, from_line, handler), 1000);

            return;
        }

        if(text.indexOf("report_end") >= 0) {
            handler.report("report end!\r");

            return;
        }

        handler.report(text);

        setTimeout(() => readReport(task_id, parseInt(data.next), handler), 1000);
    });
}