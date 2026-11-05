(function () {
  const toggle = document.getElementById("filter-toggle");
  const panel = document.getElementById("filter-panel");
  if (toggle && panel) {
    toggle.addEventListener("click", function () {
      panel.hidden = !panel.hidden;
      toggle.setAttribute("aria-expanded", String(!panel.hidden));
    });
  }

  const typeSelect = document.getElementById("venue-type");
  const discountBoxes = document.querySelectorAll("[data-discount]");
  function syncDiscounts() {
    if (!typeSelect) return;
    const allowed = typeSelect.value === "disco" || typeSelect.value === "club";
    discountBoxes.forEach(function (box) {
      box.disabled = !allowed;
      if (!allowed) box.checked = false;
    });
  }
  if (typeSelect) {
    typeSelect.addEventListener("change", syncDiscounts);
    syncDiscounts();
  }

  const picker = document.querySelector("[data-exclusive]");
  const seatsInput = document.getElementById("seats");
  const summary = document.getElementById("price-summary");
  const seatButtons = Array.prototype.slice.call(document.querySelectorAll(".seat[data-seat]"));
  const resetType = document.querySelector("[data-reset-type]");

  function selectedSet() {
    if (!seatsInput) return new Set();
    return new Set(
      seatsInput.value
        .toUpperCase()
        .split(/[^A-Z0-9-]+/)
        .map(function (item) { return item.trim(); })
        .filter(Boolean)
    );
  }

  function renderSeats() {
    const chosen = selectedSet();
    seatButtons.forEach(function (button) {
      const on = chosen.has(button.dataset.seat);
      button.classList.toggle("is-on", on);
      button.setAttribute("aria-pressed", on ? "true" : "false");
    });
    renderSummary();
  }

  function renderSummary() {
    if (!summary) return;
    const checked = picker ? picker.querySelector("input:checked:not(:disabled)") : null;
    const count = selectedSet().size;
    if (!checked || count === 0) {
      summary.textContent = "Изберете вид и седалки.";
      return;
    }
    const unit = Number(checked.dataset.price || "0");
    const total = unit * count;
    const formatted = total.toLocaleString("bg-BG", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    summary.textContent = count + " × " + checked.dataset.label + " · " + formatted + " €";
  }

  function lockType(selected) {
    if (!picker) return;
    picker.querySelectorAll("input").forEach(function (input) {
      if (input !== selected) input.disabled = true;
    });
    if (resetType) resetType.hidden = false;
    renderSummary();
  }

  function unlockType() {
    if (!picker) return;
    picker.querySelectorAll("input").forEach(function (input) {
      input.disabled = false;
      input.checked = false;
    });
    if (resetType) resetType.hidden = true;
    renderSummary();
  }

  if (picker) {
    picker.querySelectorAll("input").forEach(function (input) {
      input.addEventListener("change", function () {
        if (input.checked) lockType(input);
      });
    });
    const preset = picker.querySelector("input:checked");
    if (preset) lockType(preset);
  }
  if (resetType) {
    resetType.addEventListener("click", unlockType);
  }

  seatButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      if (!seatsInput) return;
      const chosen = selectedSet();
      const code = button.dataset.seat;
      if (chosen.has(code)) chosen.delete(code);
      else chosen.add(code);
      seatsInput.value = Array.from(chosen).join(", ");
      renderSeats();
    });
  });
  if (seatsInput) seatsInput.addEventListener("input", renderSeats);
  renderSeats();

  const eventSelect = document.getElementById("event_id");
  const typeSelect = document.getElementById("ticket_type");
  function syncTicketTypes() {
    if (!eventSelect || !typeSelect) return;
    const selected = eventSelect.selectedOptions[0];
    const allowStudent = !!(selected && selected.dataset.student === "1");
    const allowChild = !!(selected && selected.dataset.child === "1");
    typeSelect.querySelectorAll("option").forEach(function (option) {
      let allowed = true;
      if (option.value === "student") allowed = allowStudent;
      if (option.value === "child") allowed = allowChild;
      option.hidden = !allowed;
      option.disabled = !allowed;
    });
    const current = typeSelect.selectedOptions[0];
    if (current && current.disabled) typeSelect.value = "adult";
  }
  if (eventSelect && typeSelect) {
    eventSelect.addEventListener("change", syncTicketTypes);
    syncTicketTypes();
  }

  const scroller = document.querySelector("main");
  const toTop = document.getElementById("to-top");
  if (scroller && toTop) {
    scroller.addEventListener("scroll", function () {
      toTop.hidden = scroller.scrollTop < 280;
    });
    toTop.addEventListener("click", function () {
      scroller.scrollTo({ top: 0, behavior: "smooth" });
    });
  }
})();
