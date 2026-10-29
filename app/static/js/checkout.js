// Guest-group rows on the order form (C3). Without JavaScript the "Add another guest group"
// button is handled by the server instead.
(function () {
  "use strict";
  var container = document.querySelector("[data-guest-groups]");
  var addButton = document.querySelector("[data-add-group]");
  if (!container || !addButton) return;
  var MAX_GROUPS = 20;

  function groups() {
    return container.querySelectorAll("[data-guest-group]");
  }

  // Give every row consecutive indexes (guest_groups-0-label, ...) and numbers.
  function renumber() {
    var rows = groups();
    rows.forEach(function (row, index) {
      row.querySelectorAll("[name], [id], [for]").forEach(function (el) {
        ["name", "id", "for", "aria-describedby"].forEach(function (attr) {
          var value = el.getAttribute(attr);
          if (value) el.setAttribute(attr, value.replace(/guest_groups-\d+-/g, "guest_groups-" + index + "-"));
        });
      });
      row.querySelector("[data-group-number]").textContent = index + 1;
      row.querySelector("[data-remove-group]").hidden = rows.length === 1;
    });
    addButton.disabled = rows.length >= MAX_GROUPS;
  }

  addButton.addEventListener("click", function (event) {
    event.preventDefault();
    var rows = groups();
    var copy = rows[rows.length - 1].cloneNode(true);
    copy.querySelectorAll("input[type=text], input[type=number], textarea").forEach(function (el) {
      el.value = "";
      el.removeAttribute("aria-invalid");
    });
    copy.querySelectorAll("input[type=checkbox]").forEach(function (el) { el.checked = false; });
    copy.querySelectorAll(".field-errors").forEach(function (el) { el.remove(); });
    copy.querySelectorAll(".has-error").forEach(function (el) { el.classList.remove("has-error"); });
    container.appendChild(copy);
    renumber();
    copy.querySelector("input").focus();
  });

  container.addEventListener("click", function (event) {
    if (!event.target.matches("[data-remove-group]")) return;
    event.target.closest("[data-guest-group]").remove();
    renumber();
  });

  renumber();
})();
