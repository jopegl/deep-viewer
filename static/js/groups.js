document.querySelectorAll("[data-group-options]").forEach(function (input) {
  var source = document.getElementById(input.dataset.groupOptions);
  var groups = source ? JSON.parse(source.textContent) : [];

  var wrapper = document.createElement("div");
  wrapper.className = "autocomplete";
  input.parentNode.insertBefore(wrapper, input);
  wrapper.appendChild(input);

  var list = document.createElement("ul");
  list.className = "autocomplete-list";
  list.hidden = true;
  wrapper.appendChild(list);

  var active = -1;

  function close() {
    list.hidden = true;
    active = -1;
  }

  function choose(value) {
    input.value = value;
    input.classList.toggle("is-chosen", value !== "");
    input.dispatchEvent(new Event("change", {bubbles: true}));
    close();
  }

  function highlight(index) {
    list.querySelectorAll("li[data-value]").forEach(function (item, i) {
      item.classList.toggle("is-active", i === index);
    });
    active = index;
  }

  function addItem(value, label, hint, className) {
    var item = document.createElement("li");
    item.dataset.value = value;
    if (className) item.className = className;
    var name = document.createElement("span");
    name.textContent = label;
    item.appendChild(name);
    if (hint) {
      var small = document.createElement("small");
      small.textContent = hint;
      item.appendChild(small);
    }
    item.addEventListener("mousedown", function (event) {
      event.preventDefault();
      choose(value);
    });
    list.appendChild(item);
  }

  function render() {
    var query = input.value.trim();
    var lower = query.toLowerCase();
    var matches = groups.filter(function (group) {
      return group.name.toLowerCase().indexOf(lower) !== -1;
    });
    var exact = groups.some(function (group) {
      return group.name.toLowerCase() === lower;
    });

    list.innerHTML = "";
    matches.forEach(function (group) {
      var hint = group.count + (group.count === 1 ? " experimento" : " experimentos");
      addItem(group.name, group.name, hint);
    });
    if (query && !exact) {
      addItem(query, "+ Criar grupo “" + query + "”", "Grupo novo neste projeto", "autocomplete-create");
    }

    list.hidden = !list.children.length;
    active = -1;
  }

  input.addEventListener("focus", render);
  input.addEventListener("input", function () {
    input.classList.remove("is-chosen");
    render();
  });

  input.addEventListener("keydown", function (event) {
    var items = list.querySelectorAll("li[data-value]");
    if (list.hidden || !items.length) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      highlight((active + 1) % items.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      highlight((active - 1 + items.length) % items.length);
    } else if (event.key === "Enter" && active >= 0) {
      event.preventDefault();
      choose(items[active].dataset.value);
    } else if (event.key === "Escape") {
      close();
    }
  });

  input.addEventListener("blur", close);
});
