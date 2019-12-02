function renderHTML(htmlString) {
  let div = document.createElement('div');

  div.innerHTML = htmlString.trim();

  return div.firstChild;
}