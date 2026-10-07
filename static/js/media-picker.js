(function () {
  var listContainer = document.getElementById("media-picker-list");
  if (!listContainer) return;
  var refreshButton = document.getElementById("media-picker-refresh");

  function getTargetField() {
    var targetId = listContainer.dataset.targetInputId || "";
    if (!targetId) return null;
    return document.getElementById(targetId);
  }

  function renderItems(items) {
    if (!items.length) {
      listContainer.innerHTML = '<p class="text-xs text-muted">Belum ada file upload.</p>';
      return;
    }
    listContainer.innerHTML = items
      .map(function (media) {
        return (
          '<div class="rounded-lg border border-border bg-page px-3 py-2">' +
          '<p class="font-medium text-text">' + media.name + "</p>" +
          '<p class="text-xs text-muted">' + media.size + " bytes</p>" +
          '<div class="mt-2 flex flex-wrap gap-2">' +
          '<button type="button" class="btn-outline media-picker-use" data-media-path="' + media.path + '">Use Path</button>' +
          '<button type="button" class="btn-outline media-picker-copy" data-media-path="' + media.path + '">Copy Path</button>' +
          "</div></div>"
        );
      })
      .join("");
  }

  async function refreshList() {
    try {
      var response = await fetch("/api/v1/media/list?limit=20", { credentials: "same-origin" });
      if (!response.ok) return;
      var body = await response.json();
      renderItems(Array.isArray(body.data) ? body.data : []);
    } catch (error) {
      // no-op
    }
  }

  listContainer.addEventListener("click", function (event) {
    var target = event.target;
    if (!(target instanceof HTMLElement)) return;
    var path = target.dataset.mediaPath;
    if (!path) return;

    if (target.classList.contains("media-picker-copy")) {
      navigator.clipboard && navigator.clipboard.writeText(path);
      return;
    }
    if (target.classList.contains("media-picker-use")) {
      var field = getTargetField();
      if (!field) return;
      var current = field.value || "";
      field.value = current ? current + "\n" + path : path;
      field.dispatchEvent(new Event("input", { bubbles: true }));
    }
  });

  if (refreshButton) {
    refreshButton.addEventListener("click", refreshList);
  }
})();
