(function () {
  var name = document.getElementById("id_name");
  var group = document.getElementById("id_group_name");
  var fold = document.getElementById("id_fold");
  var note = document.querySelector("[data-auto-note]");
  if (!name || !group || !fold) return;

  var source = document.getElementById("group-options");
  var groups = source ? JSON.parse(source.textContent) : [];
  var pattern = /^(.*?)[\s_\-·]*(?<![a-z])fold[\s_\-]*(\d+)$/i;
  var auto = !group.value && !fold.value;

  function parse(text) {
    var match = pattern.exec(text.trim());
    if (!match) return null;
    var groupName = match[1].replace(/^[\s_\-·]+|[\s_\-·]+$/g, "");
    if (!groupName) return null;
    var known = groups.find(function (option) {
      return option.name.toLowerCase() === groupName.toLowerCase();
    });
    return {group: known ? known.name : groupName, fold: String(Number(match[2]))};
  }

  function fill() {
    if (!auto) return;
    var parsed = parse(name.value);
    group.value = parsed ? parsed.group : "";
    fold.value = parsed ? parsed.fold : "";
    group.classList.remove("is-chosen");
    if (note) note.hidden = !parsed;
  }

  function stopFilling() {
    auto = false;
    if (note) note.hidden = true;
  }

  name.addEventListener("input", fill);
  group.addEventListener("input", stopFilling);
  group.addEventListener("change", stopFilling);
  fold.addEventListener("input", stopFilling);
})();
