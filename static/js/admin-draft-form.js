(function () {
  function toSlug(value) {
    return String(value || "")
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9\s-]/g, "")
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-");
  }

  function initDraftForm(form) {
    var mode = form.dataset.mode || "create";
    var draftEntityType = form.dataset.draftEntityType || "";
    var draftEntityKey = form.dataset.draftEntityKey || "create:new";
    var slugSourceId = form.dataset.slugSourceId || "";
    var slugTargetId = form.dataset.slugTargetId || "slug";
    var autosaveNoticeId = form.dataset.autosaveNoticeId || "";
    var autosaveStatusId = form.dataset.autosaveStatusId || "";

    if (!draftEntityType) return;

    var slugSourceInput = document.getElementById(slugSourceId);
    var slugInput = document.getElementById(slugTargetId);
    var autosaveNotice = document.getElementById(autosaveNoticeId);
    var autosaveStatus = document.getElementById(autosaveStatusId);

    var userEditedSlug = mode !== "create";
    var isDirty = false;
    var saveTimer = null;

    function setStatus(level, message) {
      if (!autosaveStatus) return;
      autosaveStatus.textContent = message;
      autosaveStatus.className = "mb-4 rounded-lg border px-3 py-2 text-xs";
      if (level === "ok") {
        autosaveStatus.className += " border-emerald-200 bg-emerald-50 text-emerald-700";
        return;
      }
      if (level === "warn") {
        autosaveStatus.className += " border-amber-200 bg-amber-50 text-amber-700";
        return;
      }
      if (level === "error") {
        autosaveStatus.className += " border-red-200 bg-red-50 text-red-700";
        return;
      }
      autosaveStatus.className += " border-border bg-page text-muted";
    }

    function showNotice(message, withClearButton) {
      if (!autosaveNotice) return;
      if (!withClearButton) {
        autosaveNotice.textContent = message;
        autosaveNotice.classList.remove("hidden");
        return;
      }
      autosaveNotice.innerHTML = "";
      var text = document.createElement("span");
      text.textContent = message + " ";
      var clearBtn = document.createElement("button");
      clearBtn.type = "button";
      clearBtn.className = "font-semibold underline";
      clearBtn.textContent = "Hapus draft";
      clearBtn.addEventListener("click", function () {
        deleteDraft();
      });
      autosaveNotice.appendChild(text);
      autosaveNotice.appendChild(clearBtn);
      autosaveNotice.classList.remove("hidden");
    }

    function collectPayload() {
      var payload = {};
      var formData = new FormData(form);
      formData.forEach(function (value, key) {
        payload[key] = String(value);
      });
      return payload;
    }

    async function saveDraft() {
      var payload = collectPayload();
      setStatus("neutral", "Menyimpan draft...");
      try {
        var response = await fetch("/api/v1/drafts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({
            entity_type: draftEntityType,
            entity_key: draftEntityKey,
            payload: payload
          })
        });
        if (!response.ok) {
          setStatus("error", "Autosave gagal. Data lokal tetap ada di form ini.");
          return;
        }
        var body = await response.json();
        var savedAt = body && body.data && body.data.updated_at ? new Date(body.data.updated_at) : null;
        var savedLabel = savedAt && !Number.isNaN(savedAt.valueOf()) ? savedAt.toLocaleTimeString() : "baru saja";
        if (body && body.message === "Draft throttled") {
          setStatus("warn", "Autosave ditunda (throttle) · " + savedLabel);
        } else {
          setStatus("ok", "Draft tersimpan · " + savedLabel);
        }
      } catch (error) {
        setStatus("error", "Autosave gagal karena koneksi/server.");
      }
    }

    async function deleteDraft() {
      try {
        await fetch(
          "/api/v1/drafts?entity_type=" + encodeURIComponent(draftEntityType) + "&entity_key=" + encodeURIComponent(draftEntityKey),
          {
            method: "DELETE",
            credentials: "same-origin"
          }
        );
        if (autosaveNotice) {
          autosaveNotice.classList.add("hidden");
        }
        setStatus("neutral", "Draft server dihapus.");
      } catch (error) {
        // ignore cleanup errors
      }
    }

    async function restoreDraftIfAny() {
      var response = null;
      try {
        response = await fetch(
          "/api/v1/drafts?entity_type=" + encodeURIComponent(draftEntityType) + "&entity_key=" + encodeURIComponent(draftEntityKey),
          { credentials: "same-origin" }
        );
      } catch (error) {
        return;
      }
      if (!response || !response.ok) return;
      var body = null;
      try {
        body = await response.json();
      } catch (error) {
        return;
      }
      if (!body || !body.data || !body.data.payload) return;
      var shouldRestore = window.confirm("Ditemukan draft autosave server yang belum disimpan. Pulihkan data?");
      if (!shouldRestore) {
        return;
      }
      var payload = body.data.payload;
      Object.keys(payload).forEach(function (key) {
        var field = form.elements.namedItem(key);
        if (!field) return;
        field.value = payload[key];
      });
      isDirty = true;
      userEditedSlug = !!(slugInput && slugInput.value);
      var savedAt = body.data.updated_at ? new Date(body.data.updated_at) : null;
      var savedLabel = savedAt && !Number.isNaN(savedAt.valueOf()) ? savedAt.toLocaleString() : "sebelumnya";
      showNotice("Draft dipulihkan dari " + savedLabel + ".", true);
      setStatus("ok", "Draft berhasil dipulihkan.");
    }

    if (slugInput && slugInput.value) {
      userEditedSlug = true;
    }

    form.addEventListener("input", function () {
      isDirty = true;
      if (saveTimer) {
        clearTimeout(saveTimer);
      }
      saveTimer = setTimeout(saveDraft, 400);
    });

    if (slugSourceInput && slugInput) {
      slugSourceInput.addEventListener("input", function () {
        if (userEditedSlug) return;
        slugInput.value = toSlug(slugSourceInput.value);
      });

      slugInput.addEventListener("input", function () {
        userEditedSlug = slugInput.value.length > 0;
      });
    }

    form.addEventListener("submit", function () {
      isDirty = false;
      deleteDraft();
      setStatus("neutral", "Menyimpan data utama...");
    });

    window.addEventListener("beforeunload", function (event) {
      if (!isDirty) return;
      event.preventDefault();
      event.returnValue = "";
    });

    restoreDraftIfAny();
  }

  var forms = document.querySelectorAll("form[data-draft-entity-type]");
  forms.forEach(function (form) {
    initDraftForm(form);
  });
})();
