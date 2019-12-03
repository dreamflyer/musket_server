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