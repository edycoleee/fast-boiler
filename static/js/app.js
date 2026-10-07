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
})();
