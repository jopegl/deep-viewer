document.querySelectorAll("[data-institution-search]").forEach(function (input) {
  var wrapper = document.createElement("div");
  wrapper.className = "autocomplete";
  input.parentNode.insertBefore(wrapper, input);
  wrapper.appendChild(input);

  var list = document.createElement("ul");
  list.className = "autocomplete-list";
  list.hidden = true;
  wrapper.appendChild(list);

  var timer;
  var active = -1;

  function close() {
    list.hidden = true;
    active = -1;
  }

  function choose(value) {
    input.value = value;
    input.classList.add("is-chosen");
    close();
  }

  function highlight(index) {
    list.querySelectorAll("li[data-value]").forEach(function (item, i) {
      item.classList.toggle("is-active", i === index);
    });
    active = index;
  }

  function render(results) {
    list.innerHTML = "";
    if (!results.length) {
      var empty = document.createElement("li");
      empty.className = "autocomplete-empty";
      empty.textContent = "Nenhuma instituição encontrada";
      list.appendChild(empty);
    }
    results.forEach(function (institution) {
      var item = document.createElement("li");
      item.dataset.value = institution.name;
      var name = document.createElement("span");
      name.textContent = institution.name;
      var country = document.createElement("small");
      country.textContent = institution.country;
      item.append(name, country);
      item.addEventListener("mousedown", function (event) {
        event.preventDefault();
        choose(institution.name);
      });
      list.appendChild(item);
    });
    list.hidden = false;
    active = -1;
  }

  input.addEventListener("input", function () {
    input.classList.remove("is-chosen");
    clearTimeout(timer);
    var query = input.value.trim();
    if (query.length < 3) {
      close();
      return;
    }
    timer = setTimeout(function () {
      fetch(input.dataset.institutionSearch + "?q=" + encodeURIComponent(query))
        .then(function (response) {
          if (!response.ok) throw new Error("HTTP " + response.status);
          return response.json();
        })
        .then(function (data) {
          render(data.results);
        })
        .catch(function (error) {
          console.warn("Busca de instituições falhou:", error);
          close();
        });
    }, 300);
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