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
})();
