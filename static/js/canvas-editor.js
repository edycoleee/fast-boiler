  (function () {
    var canvas = document.getElementById("editor-canvas");
    if (!canvas) return;
    var ctx = canvas.getContext("2d");
    var toolEl = document.getElementById("tool");
    var strokeColorEl = document.getElementById("stroke-color");
    var fillColorEl = document.getElementById("fill-color");
    var lineSizeEl = document.getElementById("line-size");
    var documentSelectEl = document.getElementById("canvas-document-select");
    var canvasTitleEl = document.getElementById("canvas-title");
    var newDocumentBtn = document.getElementById("new-canvas-document");
    var renameDocumentBtn = document.getElementById("rename-canvas-document");
    var deleteDocumentBtn = document.getElementById("delete-canvas-document");
    var fontSizeEl = document.getElementById("font-size");
    var textValueEl = document.getElementById("text-value");
    var backgroundColorEl = document.getElementById("background-color");
    var applyBgBtn = document.getElementById("apply-bg");
    var undoBtn = document.getElementById("undo-canvas");
    var redoBtn = document.getElementById("redo-canvas");
    var deleteSelectedBtn = document.getElementById("delete-selected");
    var selectedInfoEl = document.getElementById("selected-info");
    var selXEl = document.getElementById("sel-x");
    var selYEl = document.getElementById("sel-y");
    var selWEl = document.getElementById("sel-w");
    var selHEl = document.getElementById("sel-h");
    var selTextEl = document.getElementById("sel-text");
    var applySelectedBtn = document.getElementById("apply-selected");
    var clearBtn = document.getElementById("clear-canvas");
    var downloadBtn = document.getElementById("download-canvas");
    var saveServerBtn = document.getElementById("save-canvas-server");
    var loadServerBtn = document.getElementById("load-canvas-server");
    var exportJsonBtn = document.getElementById("export-canvas-json");
    var importJsonBtn = document.getElementById("import-canvas-json");
    var importImageBtn = document.getElementById("import-canvas-image");
    var importImageFileEl = document.getElementById("import-canvas-image-file");
    var serverStatusEl = document.getElementById("canvas-server-status");
    var drawing = false;
    var startX = 0;
    var startY = 0;
    var draftRect = null;
    var draftPath = null;
    var selectedId = null;
    var dragState = null;
    var nextId = 1;
    var state = {
      background: "#ffffff",
      items: []
    };
    var history = [];
    var historyIndex = -1;
    var HANDLE_SIZE = 10;
    var DOCUMENT_KEY = String(window.__canvasInitialDoc || "default");
    var autoSaveSuspended = false;
    var autoSaveTimer = null;
    var AUTO_SAVE_DELAY_MS = 1200;
    var savingInProgress = false;
    var pendingAutoSave = false;
    var lastKnownUpdatedAt = null;
    var imageCache = {};

    function cloneState(inputState) {
      return JSON.parse(JSON.stringify(inputState));
    }

    function setServerStatus(text, tone) {
      if (!serverStatusEl) return;
      serverStatusEl.textContent = text;
      if (tone === "error") {
        serverStatusEl.className = "text-xs text-red-600";
      } else if (tone === "success") {
        serverStatusEl.className = "text-xs text-emerald-600";
      } else {
        serverStatusEl.className = "text-xs text-muted";
      }
    }

    function pushHistory() {
      history = history.slice(0, historyIndex + 1);
      history.push(cloneState(state));
      historyIndex = history.length - 1;
      if (!autoSaveSuspended) {
        scheduleAutoSave();
      }
    }

    function scheduleAutoSave() {
      window.clearTimeout(autoSaveTimer);
      setServerStatus("Perubahan terdeteksi. Autosave terjadwal...", "default");
      autoSaveTimer = window.setTimeout(function () {
        saveToServer(true, false);
      }, AUTO_SAVE_DELAY_MS);
    }

    function restoreHistory(index) {
      if (index < 0 || index >= history.length) return;
      state = cloneState(history[index]);
      historyIndex = index;
      selectedId = null;
      draftRect = null;
      draftPath = null;
      backgroundColorEl.value = state.background;
      render();
    }

    function createId() {
      var id = "obj-" + String(nextId);
      nextId += 1;
      return id;
    }

    function normalizeItem(rawItem) {
      if (!rawItem || typeof rawItem !== "object" || !rawItem.type) return null;
      var item = JSON.parse(JSON.stringify(rawItem));
      if (!item.id || typeof item.id !== "string") {
        item.id = createId();
      }
      if (item.type === "path" && !Array.isArray(item.points)) return null;
      if (item.type === "image") {
        if (typeof item.src !== "string" || !item.src) return null;
        item.x = Number(item.x) || 0;
        item.y = Number(item.y) || 0;
        item.w = Math.max(1, Number(item.w) || 512);
        item.h = Math.max(1, Number(item.h) || 512);
      }
      return item;
    }

    function isAllowedImageFile(file) {
      if (!file) return false;
      var name = String(file.name || "").toLowerCase();
      var type = String(file.type || "").toLowerCase();
      var isAllowedExt = /\.(jpg|jpeg|png|bmp)$/.test(name);
      var isAllowedMime = type === "image/jpeg" || type === "image/png" || type === "image/bmp";
      return isAllowedExt || isAllowedMime;
    }

    function readFileAsDataUrl(file) {
      return new Promise(function (resolve, reject) {
        var reader = new FileReader();
        reader.onload = function () {
          resolve(String(reader.result || ""));
        };
        reader.onerror = function () {
          reject(new Error("read-failed"));
        };
        reader.readAsDataURL(file);
      });
    }

    function loadImageFromDataUrl(dataUrl) {
      return new Promise(function (resolve, reject) {
        var image = new Image();
        image.onload = function () {
          resolve(image);
        };
        image.onerror = function () {
          reject(new Error("image-load-failed"));
        };
        image.src = dataUrl;
      });
    }

    async function resizeFileToDataUrl512(file) {
      var sourceDataUrl = await readFileAsDataUrl(file);
      var image = await loadImageFromDataUrl(sourceDataUrl);
      var tempCanvas = document.createElement("canvas");
      tempCanvas.width = 512;
      tempCanvas.height = 512;
      var tempCtx = tempCanvas.getContext("2d");
      if (!tempCtx) throw new Error("canvas-not-supported");
      tempCtx.fillStyle = "#ffffff";
      tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
      tempCtx.drawImage(image, 0, 0, 512, 512);

      var quality = 0.9;
      var output = tempCanvas.toDataURL("image/jpeg", quality);
      while (output.length > 100000 && quality > 0.35) {
        quality -= 0.1;
        output = tempCanvas.toDataURL("image/jpeg", quality);
      }
      return output;
    }

    function applyCanvasState(nextState, pushToHistory) {
      var normalized = { background: "#ffffff", items: [] };
      if (nextState && typeof nextState === "object") {
        if (typeof nextState.background === "string") normalized.background = nextState.background;
        if (Array.isArray(nextState.items)) {
          normalized.items = nextState.items.map(normalizeItem).filter(Boolean);
        }
      }
      state = normalized;
      selectedId = null;
      draftRect = null;
      draftPath = null;
      backgroundColorEl.value = state.background;
      var maxNumericId = 0;
      state.items.forEach(function (item) {
        var match = /^obj-(\d+)$/.exec(item.id || "");
        if (!match) return;
        var num = Number(match[1]);
        if (!Number.isNaN(num) && num > maxNumericId) maxNumericId = num;
      });
      nextId = maxNumericId + 1;
      if (pushToHistory) pushHistory();
      render();
    }

    async function saveToServer(isAutoSave, forceSave) {
      if (savingInProgress) {
        pendingAutoSave = true;
        return;
      }
      savingInProgress = true;
      setServerStatus(isAutoSave ? "Autosave ke server..." : "Menyimpan ke server...", "default");
      var payload = {
        document_key: DOCUMENT_KEY,
        title: (canvasTitleEl.value || "Untitled Canvas").trim() || "Untitled Canvas",
        payload: cloneState(state),
        last_known_updated_at: lastKnownUpdatedAt,
        force: !!forceSave
      };
      try {
        var response = await fetch("/api/v1/canvas", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        var data = await response.json();
        if (response.status === 409 && !forceSave) {
          setServerStatus("Konflik: dokumen berubah di tab/device lain.", "error");
          var overwrite = window.confirm("Dokumen di server lebih baru. Timpa dengan versi Anda?");
          if (overwrite) {
            savingInProgress = false;
            return saveToServer(isAutoSave, true);
          }
          return;
        }
        if (!response.ok || !data.success) throw new Error((data && data.message) || "Save gagal");
        lastKnownUpdatedAt = data && data.data ? data.data.updated_at : lastKnownUpdatedAt;
        setServerStatus(isAutoSave ? "Autosave tersimpan." : "Canvas tersimpan ke server.", "success");
        await loadDocumentList(DOCUMENT_KEY);
      } catch (err) {
        setServerStatus(isAutoSave ? "Autosave gagal." : "Gagal simpan ke server.", "error");
      } finally {
        savingInProgress = false;
        if (pendingAutoSave) {
          pendingAutoSave = false;
          saveToServer(true, false);
        }
      }
    }

    async function loadFromServer() {
      setServerStatus("Memuat dari server...", "default");
      try {
        var response = await fetch("/api/v1/canvas?document_key=" + encodeURIComponent(DOCUMENT_KEY));
        var data = await response.json();
        if (!response.ok || !data.success) throw new Error((data && data.message) || "Load gagal");
        if (!data.data || !data.data.payload) {
          lastKnownUpdatedAt = null;
          setServerStatus("Belum ada data canvas di server.", "default");
          return;
        }
        canvasTitleEl.value = data.data.title || canvasTitleEl.value;
        lastKnownUpdatedAt = data.data.updated_at || null;
        autoSaveSuspended = true;
        applyCanvasState(data.data.payload, true);
        autoSaveSuspended = false;
        setServerStatus("Canvas dimuat dari server.", "success");
      } catch (err) {
        setServerStatus("Gagal memuat dari server.", "error");
        autoSaveSuspended = false;
      }
    }

    async function loadDocumentList(preferredKey) {
      try {
        var response = await fetch("/api/v1/canvas/documents?limit=100");
        var data = await response.json();
        if (!response.ok || !data.success) throw new Error("Load documents gagal");
        var docs = Array.isArray(data.data) ? data.data : [];
        if (!docs.some(function (doc) { return doc.document_key === DOCUMENT_KEY; })) {
          docs.unshift({
            document_key: DOCUMENT_KEY,
            title: canvasTitleEl.value || "Untitled Canvas"
          });
        }
        documentSelectEl.innerHTML = "";
        docs.forEach(function (doc) {
          var option = document.createElement("option");
          option.value = doc.document_key;
          option.textContent = doc.document_key + " - " + (doc.title || "Untitled Canvas");
          documentSelectEl.appendChild(option);
        });
        var nextValue = preferredKey || DOCUMENT_KEY;
        documentSelectEl.value = nextValue;
        if (window.history && window.history.replaceState) {
          var nextUrl = new URL(window.location.href);
          nextUrl.searchParams.set("doc", nextValue);
          window.history.replaceState({}, "", nextUrl.toString());
        }
      } catch (err) {
        setServerStatus("Gagal memuat daftar dokumen.", "error");
      }
    }

    async function renameCurrentDocument() {
      if (!DOCUMENT_KEY) return;
      var newKeyInput = window.prompt("Document key baru:", DOCUMENT_KEY);
      if (!newKeyInput) return;
      var newKey = newKeyInput.trim().toLowerCase().replace(/[^a-z0-9\-_]/g, "-");
      if (!newKey) {
        setServerStatus("Document key tidak valid.", "error");
        return;
      }
      var newTitleInput = window.prompt("Title dokumen:", canvasTitleEl.value || "Untitled Canvas");
      if (!newTitleInput) return;
      var newTitle = (newTitleInput || "").trim() || "Untitled Canvas";
      setServerStatus("Mengubah dokumen...", "default");
      try {
        var response = await fetch("/api/v1/canvas", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            document_key: DOCUMENT_KEY,
            new_document_key: newKey,
            title: newTitle
          })
        });
        var data = await response.json();
        if (!response.ok || !data.success) throw new Error((data && data.message) || "Rename gagal");
        DOCUMENT_KEY = newKey;
        canvasTitleEl.value = newTitle;
        lastKnownUpdatedAt = data && data.data ? data.data.updated_at : lastKnownUpdatedAt;
        await loadDocumentList(DOCUMENT_KEY);
        setServerStatus("Dokumen berhasil diubah.", "success");
      } catch (err) {
        setServerStatus("Gagal mengubah dokumen.", "error");
      }
    }

    async function deleteCurrentDocument() {
      if (!DOCUMENT_KEY) return;
      var confirmed = window.confirm("Hapus dokumen '" + DOCUMENT_KEY + "'?");
      if (!confirmed) return;
      setServerStatus("Menghapus dokumen...", "default");
      try {
        var response = await fetch("/api/v1/canvas?document_key=" + encodeURIComponent(DOCUMENT_KEY), {
          method: "DELETE"
        });
        var data = await response.json();
        if (!response.ok || !data.success) throw new Error((data && data.message) || "Delete gagal");
        DOCUMENT_KEY = "default";
        canvasTitleEl.value = "Main Canvas";
        lastKnownUpdatedAt = null;
        autoSaveSuspended = true;
        applyCanvasState({ background: "#ffffff", items: [] }, true);
        autoSaveSuspended = false;
        await loadDocumentList(DOCUMENT_KEY);
        setServerStatus("Dokumen berhasil dihapus.", "success");
      } catch (err) {
        setServerStatus("Gagal menghapus dokumen.", "error");
      }
    }

    function getPos(e) {
      var rect = canvas.getBoundingClientRect();
      var scaleX = canvas.width / rect.width;
      var scaleY = canvas.height / rect.height;
      return {
        x: (e.clientX - rect.left) * scaleX,
        y: (e.clientY - rect.top) * scaleY
      };
    }

    function applyStyle() {
      ctx.strokeStyle = strokeColorEl.value;
      ctx.fillStyle = fillColorEl.value;
      ctx.lineWidth = Math.max(1, parseInt(lineSizeEl.value || "1", 10));
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.font = Math.max(10, parseInt(fontSizeEl.value || "20", 10)) + "px sans-serif";
    }

    function getBounds(item) {
      if (item.type === "rect") {
        return { x: item.x, y: item.y, w: item.w, h: item.h };
      }
      if (item.type === "text") {
        ctx.save();
        ctx.font = Math.max(10, item.fontSize || 20) + "px sans-serif";
        var width = ctx.measureText(item.text || "").width || 10;
        ctx.restore();
        return { x: item.x, y: item.y - (item.fontSize || 20), w: width, h: item.fontSize || 20 };
      }
      if (item.type === "image") {
        return {
          x: Number(item.x) || 0,
          y: Number(item.y) || 0,
          w: Math.max(1, Number(item.w) || 512),
          h: Math.max(1, Number(item.h) || 512)
        };
      }
      if (item.type === "path") {
        var minX = Infinity;
        var minY = Infinity;
        var maxX = -Infinity;
        var maxY = -Infinity;
        for (var i = 0; i < item.points.length; i += 1) {
          var point = item.points[i];
          minX = Math.min(minX, point.x);
          minY = Math.min(minY, point.y);
          maxX = Math.max(maxX, point.x);
          maxY = Math.max(maxY, point.y);
        }
        if (!isFinite(minX)) {
          return { x: item.x || 0, y: item.y || 0, w: 1, h: 1 };
        }
        var pad = Math.max(2, item.size || 1);
        return { x: minX - pad, y: minY - pad, w: maxX - minX + pad * 2, h: maxY - minY + pad * 2 };
      }
      return { x: 0, y: 0, w: 0, h: 0 };
    }

    function drawSelection(item) {
      if (!item) return;
      var b = getBounds(item);
      ctx.save();
      ctx.strokeStyle = "#2563eb";
      ctx.setLineDash([6, 4]);
      ctx.strokeRect(b.x, b.y, b.w, b.h);
      ctx.setLineDash([]);
      if (item.type !== "path") {
        ctx.fillStyle = "#2563eb";
        ctx.fillRect(b.x + b.w - HANDLE_SIZE, b.y + b.h - HANDLE_SIZE, HANDLE_SIZE, HANDLE_SIZE);
      }
      ctx.restore();
    }

    function drawItem(item) {
      if (item.type === "path") {
        if (!item.points || item.points.length < 2) return;
        ctx.save();
        ctx.strokeStyle = item.stroke;
        ctx.lineWidth = item.size;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.beginPath();
        ctx.moveTo(item.points[0].x, item.points[0].y);
        for (var i = 1; i < item.points.length; i += 1) {
          ctx.lineTo(item.points[i].x, item.points[i].y);
        }
        ctx.stroke();
        ctx.restore();
        return;
      }
      if (item.type === "rect") {
        ctx.save();
        ctx.strokeStyle = item.stroke;
        ctx.fillStyle = item.fill;
        ctx.lineWidth = item.size;
        ctx.fillRect(item.x, item.y, item.w, item.h);
        ctx.strokeRect(item.x, item.y, item.w, item.h);
        ctx.restore();
        return;
      }
      if (item.type === "text") {
        ctx.save();
        ctx.fillStyle = item.color;
        ctx.font = Math.max(10, item.fontSize || 20) + "px sans-serif";
        ctx.fillText(item.text || "", item.x, item.y);
        ctx.restore();
        return;
      }
      if (item.type === "image") {
        if (!item.src) return;
        var cacheKey = String(item.id || item.src);
        var cached = imageCache[cacheKey];
        if (cached && cached.ready && cached.image) {
          ctx.drawImage(cached.image, item.x, item.y, item.w, item.h);
          return;
        }
        if (!cached) {
          var img = new Image();
          imageCache[cacheKey] = { image: img, ready: false };
          img.onload = function () {
            imageCache[cacheKey].ready = true;
            render();
          };
          img.onerror = function () {
            delete imageCache[cacheKey];
          };
          img.src = item.src;
        }
        return;
      }
    }

    function render() {
      ctx.save();
      ctx.fillStyle = state.background;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.restore();

      for (var i = 0; i < state.items.length; i += 1) {
        drawItem(state.items[i]);
      }

      if (draftRect) {
        drawItem(draftRect);
      }
      if (draftPath) {
        drawItem(draftPath);
      }

      if (selectedId) {
        for (var j = 0; j < state.items.length; j += 1) {
          if (state.items[j].id === selectedId) {
            drawSelection(state.items[j]);
            break;
          }
        }
      }
      syncSelectedPanel();
    }

    function getItemById(id) {
      for (var i = 0; i < state.items.length; i += 1) {
        if (state.items[i].id === id) return state.items[i];
      }
      return null;
    }

    function syncSelectedPanel() {
      var item = selectedId ? getItemById(selectedId) : null;
      if (!item) {
        selectedInfoEl.textContent = "Belum ada objek terpilih.";
        selXEl.value = "";
        selYEl.value = "";
        selWEl.value = "";
        selHEl.value = "";
        selTextEl.value = "";
        return;
      }
      var b = getBounds(item);
      selectedInfoEl.textContent = "Terpilih: " + item.type + " (" + item.id + ")";
      selXEl.value = Math.round(b.x);
      selYEl.value = Math.round(b.y);
      selWEl.value = Math.round(Math.max(1, b.w));
      selHEl.value = Math.round(Math.max(1, b.h));
      if (item.type === "text") {
        selTextEl.value = item.text || "";
      } else {
        selTextEl.value = "";
      }
    }

    function normalizeRect(rect) {
      var x = rect.x;
      var y = rect.y;
      var w = rect.w;
      var h = rect.h;
      if (w < 0) {
        x = x + w;
        w = Math.abs(w);
      }
      if (h < 0) {
        y = y + h;
        h = Math.abs(h);
      }
      rect.x = x;
      rect.y = y;
      rect.w = w;
      rect.h = h;
    }

    function isInside(bounds, x, y) {
      return x >= bounds.x && y >= bounds.y && x <= bounds.x + bounds.w && y <= bounds.y + bounds.h;
    }

    function hitTest(x, y) {
      for (var i = state.items.length - 1; i >= 0; i -= 1) {
        var item = state.items[i];
        var bounds = getBounds(item);
        if (isInside(bounds, x, y)) {
          var onResizeHandle =
            item.type !== "path" &&
            x >= bounds.x + bounds.w - HANDLE_SIZE &&
            y >= bounds.y + bounds.h - HANDLE_SIZE &&
            x <= bounds.x + bounds.w &&
            y <= bounds.y + bounds.h;
          return { item: item, resize: onResizeHandle, bounds: bounds };
        }
      }
      return null;
    }

    function moveItem(item, dx, dy) {
      if (item.type === "path") {
        for (var i = 0; i < item.points.length; i += 1) {
          item.points[i].x += dx;
          item.points[i].y += dy;
        }
        return;
      }
      item.x += dx;
      item.y += dy;
    }

    function resizeItem(item, startBounds, dx, dy) {
      if (item.type === "rect") {
        item.w = Math.max(20, startBounds.w + dx);
        item.h = Math.max(20, startBounds.h + dy);
        return;
      }
      if (item.type === "image") {
        item.w = Math.max(20, startBounds.w + dx);
        item.h = Math.max(20, startBounds.h + dy);
        return;
      }
      if (item.type === "text") {
        item.fontSize = Math.max(10, Math.round((item.fontSize || 20) + dy * 0.2));
        return;
      }
    }

    canvas.addEventListener("mousedown", function (e) {
      applyStyle();
      var pos = getPos(e);
      startX = pos.x;
      startY = pos.y;
      var tool = toolEl.value;

      if (tool === "select") {
        var hit = hitTest(pos.x, pos.y);
        if (!hit) {
          selectedId = null;
          dragState = null;
          render();
          return;
        }
        selectedId = hit.item.id;
        dragState = {
          mode: hit.resize ? "resize" : "move",
          itemId: hit.item.id,
          startX: pos.x,
          startY: pos.y,
          startBounds: {
            x: hit.bounds.x,
            y: hit.bounds.y,
            w: hit.bounds.w,
            h: hit.bounds.h
          }
        };
        render();
        return;
      }

      if (tool === "text") {
        var text = textValueEl.value || "Contoh teks";
        if (text) {
          state.items.push({
            id: createId(),
            type: "text",
            x: startX,
            y: startY,
            text: text,
            color: strokeColorEl.value,
            fontSize: Math.max(10, parseInt(fontSizeEl.value || "20", 10))
          });
          pushHistory();
          render();
        }
        return;
      }

      drawing = true;
      if (tool === "draw") {
        draftPath = {
          id: createId(),
          type: "path",
          stroke: strokeColorEl.value,
          size: Math.max(1, parseInt(lineSizeEl.value || "1", 10)),
          points: [{ x: startX, y: startY }]
        };
      } else if (tool === "rect") {
        draftRect = {
          id: createId(),
          type: "rect",
          x: startX,
          y: startY,
          w: 0,
          h: 0,
          stroke: strokeColorEl.value,
          fill: fillColorEl.value,
          size: Math.max(1, parseInt(lineSizeEl.value || "1", 10))
        };
      }
    });

    canvas.addEventListener("mousemove", function (e) {
      var pos = getPos(e);
      if (dragState && toolEl.value === "select") {
        var selectedItem = getItemById(dragState.itemId);
        if (!selectedItem) return;
        var dx = pos.x - dragState.startX;
        var dy = pos.y - dragState.startY;
        if (dragState.mode === "move") {
          moveItem(selectedItem, dx, dy);
          dragState.startX = pos.x;
          dragState.startY = pos.y;
        } else {
          resizeItem(selectedItem, dragState.startBounds, dx, dy);
        }
        render();
        return;
      }

      if (!drawing) return;
      if (draftPath) {
        draftPath.points.push({ x: pos.x, y: pos.y });
        render();
        return;
      }
      if (draftRect) {
        draftRect.w = pos.x - startX;
        draftRect.h = pos.y - startY;
        render();
      }
    });

    function stopDrawing() {
      if (dragState) {
        dragState = null;
        pushHistory();
        render();
        return;
      }

      if (!drawing) return;
      drawing = false;
      if (draftPath && draftPath.points.length > 1) {
        state.items.push(draftPath);
        draftPath = null;
        pushHistory();
        render();
        return;
      }
      if (draftRect) {
        normalizeRect(draftRect);
        if (draftRect.w >= 1 && draftRect.h >= 1) {
          state.items.push(draftRect);
          draftRect = null;
          pushHistory();
          render();
          return;
        }
        draftRect = null;
      }
      render();
    }

    canvas.addEventListener("mouseup", stopDrawing);
    canvas.addEventListener("mouseleave", stopDrawing);

    applyBgBtn.addEventListener("click", function () {
      state.background = backgroundColorEl.value;
      pushHistory();
      render();
    });

    applySelectedBtn.addEventListener("click", function () {
      var item = selectedId ? getItemById(selectedId) : null;
      if (!item) return;
      var nextX = Number(selXEl.value);
      var nextY = Number(selYEl.value);
      var nextW = Number(selWEl.value);
      var nextH = Number(selHEl.value);
      var nextText = selTextEl.value;

      if (item.type !== "path") {
        if (!Number.isNaN(nextX)) item.x = nextX;
        if (!Number.isNaN(nextY)) item.y = nextY;
      }

      if (item.type === "rect") {
        if (!Number.isNaN(nextW)) item.w = Math.max(20, nextW);
        if (!Number.isNaN(nextH)) item.h = Math.max(20, nextH);
      }

      if (item.type === "image") {
        if (!Number.isNaN(nextW)) item.w = Math.max(20, nextW);
        if (!Number.isNaN(nextH)) item.h = Math.max(20, nextH);
      }

      if (item.type === "text") {
        item.text = nextText || item.text;
      } else if (item.type === "path") {
        var currentBounds = getBounds(item);
        var pathDx = 0;
        var pathDy = 0;
        if (!Number.isNaN(nextX)) pathDx = nextX - currentBounds.x;
        if (!Number.isNaN(nextY)) pathDy = nextY - currentBounds.y;
        moveItem(item, pathDx, pathDy);
      }

      pushHistory();
      render();
    });

    undoBtn.addEventListener("click", function () {
      restoreHistory(historyIndex - 1);
    });

    redoBtn.addEventListener("click", function () {
      restoreHistory(historyIndex + 1);
    });

    deleteSelectedBtn.addEventListener("click", function () {
      if (!selectedId) return;
      state.items = state.items.filter(function (item) {
        return item.id !== selectedId;
      });
      selectedId = null;
      pushHistory();
      render();
    });

    clearBtn.addEventListener("click", function () {
      state.items = [];
      selectedId = null;
      pushHistory();
      render();
    });

    downloadBtn.addEventListener("click", function () {
      var link = document.createElement("a");
      link.href = canvas.toDataURL("image/png");
      link.download = "canvas-export.png";
      link.click();
    });

    saveServerBtn.addEventListener("click", function () {
      saveToServer(false, false);
    });

    loadServerBtn.addEventListener("click", function () {
      loadFromServer();
    });

    documentSelectEl.addEventListener("change", function () {
      DOCUMENT_KEY = documentSelectEl.value || "default";
      loadFromServer();
    });

    newDocumentBtn.addEventListener("click", function () {
      var rawKey = window.prompt("Document key baru (contoh: homepage-layout):", "");
      if (!rawKey) return;
      var key = rawKey.trim().toLowerCase().replace(/[^a-z0-9\-_]/g, "-");
      if (!key) {
        setServerStatus("Document key tidak valid.", "error");
        return;
      }
      var rawTitle = window.prompt("Title dokumen:", "Untitled Canvas");
      DOCUMENT_KEY = key;
      canvasTitleEl.value = (rawTitle || "Untitled Canvas").trim() || "Untitled Canvas";
      lastKnownUpdatedAt = null;
      autoSaveSuspended = true;
      applyCanvasState({ background: "#ffffff", items: [] }, true);
      autoSaveSuspended = false;
      loadDocumentList(DOCUMENT_KEY);
      setServerStatus("Dokumen baru siap diedit.", "success");
    });

    renameDocumentBtn.addEventListener("click", function () {
      renameCurrentDocument();
    });

    deleteDocumentBtn.addEventListener("click", function () {
      deleteCurrentDocument();
    });

    canvasTitleEl.addEventListener("change", function () {
      scheduleAutoSave();
    });

    exportJsonBtn.addEventListener("click", function () {
      var link = document.createElement("a");
      var blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
      link.href = URL.createObjectURL(blob);
      link.download = "canvas-export.json";
      link.click();
      URL.revokeObjectURL(link.href);
    });

    importJsonBtn.addEventListener("click", function () {
      var rawJson = window.prompt("Paste JSON canvas:");
      if (!rawJson) return;
      try {
        var parsed = JSON.parse(rawJson);
        applyCanvasState(parsed, true);
        setServerStatus("Canvas JSON berhasil di-import.", "success");
      } catch (err) {
        setServerStatus("JSON tidak valid.", "error");
      }
    });

    if (importImageBtn && importImageFileEl) {
      importImageBtn.addEventListener("click", function () {
        importImageFileEl.click();
      });

      importImageFileEl.addEventListener("change", async function () {
        var file = importImageFileEl.files && importImageFileEl.files[0] ? importImageFileEl.files[0] : null;
        importImageFileEl.value = "";
        if (!file) return;
        if (!isAllowedImageFile(file)) {
          setServerStatus("Format gambar harus JPG, PNG, atau BMP.", "error");
          return;
        }
        try {
          setServerStatus("Memproses gambar 512x512...", "default");
          var dataUrl = await resizeFileToDataUrl512(file);
          var item = {
            id: createId(),
            type: "image",
            x: Math.max(0, Math.round((canvas.width - 512) / 2)),
            y: Math.max(0, Math.round((canvas.height - 512) / 2)),
            w: 512,
            h: 512,
            src: dataUrl
          };
          state.items.push(item);
          selectedId = item.id;
          pushHistory();
          render();
          setServerStatus("Gambar berhasil diimport ke canvas (512x512).", "success");
        } catch (error) {
          setServerStatus("Gagal memproses gambar.", "error");
        }
      });
    }

    canvas.addEventListener("dblclick", function (e) {
      if (toolEl.value !== "select") return;
      var pos = getPos(e);
      var hit = hitTest(pos.x, pos.y);
      if (!hit || hit.item.type !== "text") return;
      var nextText = window.prompt("Ubah teks:", hit.item.text || "");
      if (nextText === null) return;
      hit.item.text = nextText;
      pushHistory();
      render();
    });

    window.addEventListener("keydown", function (event) {
      var targetTag = (event.target && event.target.tagName || "").toLowerCase();
      if (targetTag === "input" || targetTag === "textarea" || targetTag === "select") return;
      var key = event.key.toLowerCase();
      if ((event.ctrlKey || event.metaKey) && key === "z") {
        event.preventDefault();
        restoreHistory(historyIndex - 1);
      }
      if ((event.ctrlKey || event.metaKey) && key === "y") {
        event.preventDefault();
        restoreHistory(historyIndex + 1);
      }
      if (key === "delete" || key === "backspace") {
        if (!selectedId) return;
        event.preventDefault();
        state.items = state.items.filter(function (item) {
          return item.id !== selectedId;
        });
        selectedId = null;
        pushHistory();
        render();
      }
    });

    state.background = backgroundColorEl.value;
    autoSaveSuspended = true;
    pushHistory();
    render();
    autoSaveSuspended = false;
    loadDocumentList(DOCUMENT_KEY).then(function () {
      loadFromServer();
    });
  })();
