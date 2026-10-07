(function () {
  var key = "fast-boiler-theme";
  var root = document.documentElement;

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme || "default");
  }

  window.setTheme = function setTheme(theme) {
    applyTheme(theme);
    try {
      localStorage.setItem(key, theme);
    } catch (error) {
      // Ignore localStorage write failures in restricted environments.
    }
  };

  try {
    var saved = localStorage.getItem(key);
    if (saved) {
      applyTheme(saved);
    }
  } catch (error) {
    applyTheme("default");
  }

  document.addEventListener("click", function (event) {
    var toastClose = event.target.closest("[data-dismiss-toast]");
    if (toastClose) {
      var toast = toastClose.closest('[role="status"]');
      if (toast) {
        toast.remove();
      }
      return;
    }

    var openDialogButton = event.target.closest("[data-dialog-open]");
    if (openDialogButton) {
      var targetId = openDialogButton.getAttribute("data-dialog-open");
      if (!targetId) return;
      var dialog = document.getElementById(targetId);
      if (dialog && typeof dialog.showModal === "function") {
        dialog.showModal();
      }
      return;
    }

    var closeDialogButton = event.target.closest("[data-dialog-close]");
    if (closeDialogButton) {
      var closeId = closeDialogButton.getAttribute("data-dialog-close");
      if (!closeId) return;
      var closeDialog = document.getElementById(closeId);
      if (closeDialog && typeof closeDialog.close === "function") {
        closeDialog.close();
      }
      return;
    }

    var confirmButton = event.target.closest("[data-confirm-submit-id]");
    if (confirmButton) {
      var formId = confirmButton.getAttribute("data-confirm-submit-id");
      if (!formId) return;
      var form = document.getElementById(formId);
      if (form && typeof form.requestSubmit === "function") {
        form.requestSubmit();
      } else if (form) {
        form.submit();
      }
      var parentDialog = confirmButton.closest("dialog");
      if (parentDialog && typeof parentDialog.close === "function") {
        parentDialog.close();
      }
    }
  });

  document.addEventListener("click", function (event) {
    var tabTrigger = event.target.closest("[data-tab-trigger]");
    if (!tabTrigger) return;
    var tabContainer = tabTrigger.closest("[data-tabs]");
    if (!tabContainer) return;
    var targetId = tabTrigger.getAttribute("data-tab-target");
    if (!targetId) return;

    var allTriggers = tabContainer.querySelectorAll("[data-tab-trigger]");
    for (var i = 0; i < allTriggers.length; i += 1) {
      allTriggers[i].setAttribute("aria-selected", "false");
      allTriggers[i].classList.remove("tab-btn-active");
    }
    tabTrigger.setAttribute("aria-selected", "true");
    tabTrigger.classList.add("tab-btn-active");

    var panels = tabContainer.querySelectorAll("[data-tab-panel]");
    for (var j = 0; j < panels.length; j += 1) {
      panels[j].setAttribute("hidden", "");
    }
    var targetPanel = document.getElementById(targetId);
    if (targetPanel) {
      targetPanel.removeAttribute("hidden");
    }
  });

  function updateTableSelectionCount(container, table) {
    var countNode = container.querySelector("[data-selected-count]");
    if (!countNode) return;
    var rows = table.querySelectorAll("[data-row-select]");
    var selected = 0;
    for (var i = 0; i < rows.length; i += 1) {
      if (rows[i].checked) selected += 1;
    }
    countNode.textContent = String(selected);
  }

  function setColumnVisibility(table, columnKey, visible) {
    var cells = table.querySelectorAll('[data-col="' + columnKey + '"]');
    for (var i = 0; i < cells.length; i += 1) {
      cells[i].hidden = !visible;
    }
  }

  document.addEventListener("change", function (event) {
    var tableControls = event.target.closest("[data-table-controls]");
    if (!tableControls) return;

    var targetTableId = tableControls.getAttribute("data-table-controls");
    if (!targetTableId) return;
    var table = document.getElementById(targetTableId);
    if (!table) return;

    var selectAll = event.target.closest("[data-select-all]");
    if (selectAll) {
      var rowChecks = table.querySelectorAll("[data-row-select]");
      for (var i = 0; i < rowChecks.length; i += 1) {
        rowChecks[i].checked = selectAll.checked;
      }
      updateTableSelectionCount(tableControls, table);
      return;
    }

    var colToggle = event.target.closest("[data-col-toggle]");
    if (colToggle) {
      var key = colToggle.getAttribute("data-col-toggle");
      if (!key) return;
      setColumnVisibility(table, key, colToggle.checked);
      return;
    }
  });

  document.addEventListener("change", function (event) {
    var rowSelect = event.target.closest("[data-row-select]");
    if (!rowSelect) return;
    var table = rowSelect.closest("table");
    if (!table || !table.id) return;
    var controls = document.querySelector('[data-table-controls="' + table.id + '"]');
    if (!controls) return;
    updateTableSelectionCount(controls, table);
  });
})();
