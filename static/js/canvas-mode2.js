(function () {
  var canvas = document.getElementById("mode2-canvas");
  if (!canvas) return;
  var ctx = canvas.getContext("2d");
  if (!ctx) return;

  var importBtn = document.getElementById("mode2-import-btn");
  var importFile = document.getElementById("mode2-import-file");
  var undoBtn = document.getElementById("mode2-undo-btn");
  var previewBtn = document.getElementById("mode2-preview-btn");
  var previewDownloadBtn = document.getElementById("mode2-preview-download-btn");
  var clearBtn = document.getElementById("mode2-clear-btn");
  var clearRegionsBtn = document.getElementById("mode2-clear-regions-btn");
  var downloadBtn = document.getElementById("mode2-download-btn");
  var copyJsonBtn = document.getElementById("mode2-copy-json-btn");
  var statusEl = document.getElementById("mode2-status");
  var regionsJsonEl = document.getElementById("mode2-regions-json");
  var previewCanvas = document.getElementById("mode2-preview-canvas");
  var previewCtx = previewCanvas ? previewCanvas.getContext("2d") : null;

  var backgroundImage = null;
  var regions = [];
  var regionSeq = 1;
  var draftPoints = [];
  var drawing = false;
  var history = [];
  var HISTORY_LIMIT = 30;
  var previewEnabled = false;

  function setStatus(message, tone) {
    if (!statusEl) return;
    statusEl.textContent = message;
    if (tone === "error") {
      statusEl.className = "mb-2 text-xs text-red-600";
      return;
    }
    if (tone === "success") {
      statusEl.className = "mb-2 text-xs text-emerald-600";
      return;
    }
    statusEl.className = "mb-2 text-xs text-muted";
  }

  function clearCanvasBase() {
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  function isAllowedImage(file) {
    if (!file) return false;
    var name = String(file.name || "").toLowerCase();
    var type = String(file.type || "").toLowerCase();
    var extAllowed = /\.(jpg|jpeg|png|bmp)$/.test(name);
    var mimeAllowed = type === "image/jpeg" || type === "image/png" || type === "image/bmp";
    return extAllowed || mimeAllowed;
  }

  function readDataUrl(file) {
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

  function loadImage(dataUrl) {
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

  function renderRegion(targetCtx, region, isDraft, showLabel) {
    if (!region.points || region.points.length < 2) return;
    targetCtx.save();
    targetCtx.strokeStyle = isDraft ? "#2563eb" : "#dc2626";
    targetCtx.lineWidth = 2;
    targetCtx.setLineDash(isDraft ? [6, 4] : []);
    targetCtx.fillStyle = isDraft ? "rgba(37, 99, 235, 0.12)" : "rgba(220, 38, 38, 0.15)";
    targetCtx.beginPath();
    targetCtx.moveTo(region.points[0].x, region.points[0].y);
    for (var i = 1; i < region.points.length; i += 1) {
      targetCtx.lineTo(region.points[i].x, region.points[i].y);
    }
    targetCtx.closePath();
    if (!isDraft) {
      targetCtx.fill();
    }
    targetCtx.stroke();
    if (showLabel && !isDraft && region.points.length > 0) {
      targetCtx.fillStyle = "#111827";
      targetCtx.font = "12px sans-serif";
      targetCtx.fillText("R" + region.id, region.points[0].x + 4, Math.max(12, region.points[0].y - 6));
    }
    targetCtx.restore();
  }

  function clonePoints(points) {
    var copied = [];
    for (var i = 0; i < points.length; i += 1) {
      copied.push({ x: points[i].x, y: points[i].y });
    }
    return copied;
  }

  function cloneRegions(sourceRegions) {
    var copied = [];
    for (var i = 0; i < sourceRegions.length; i += 1) {
      copied.push({
        id: sourceRegions[i].id,
        points: clonePoints(sourceRegions[i].points || [])
      });
    }
    return copied;
  }

  function pushHistory() {
    history.push({
      backgroundImage: backgroundImage,
      regions: cloneRegions(regions),
      regionSeq: regionSeq
    });
    if (history.length > HISTORY_LIMIT) {
      history.shift();
    }
  }

  function restoreFromSnapshot(snapshot) {
    backgroundImage = snapshot.backgroundImage || null;
    regions = cloneRegions(snapshot.regions || []);
    regionSeq = typeof snapshot.regionSeq === "number" ? snapshot.regionSeq : 1;
    draftPoints = [];
    drawing = false;
    syncRegionsJson();
    renderCanvas();
  }

  function renderCanvas() {
    clearCanvasBase();
    if (backgroundImage) {
      ctx.drawImage(backgroundImage, 0, 0, 512, 512);
    }
    for (var i = 0; i < regions.length; i += 1) {
      renderRegion(ctx, regions[i], false, true);
    }
    if (draftPoints.length >= 2) {
      renderRegion(ctx, { points: draftPoints }, true, false);
    }
    if (previewEnabled) {
      renderRegionsOnlyPreview();
    }
  }

  function clearPreviewCanvas() {
    if (!previewCtx || !previewCanvas) return;
    previewCtx.fillStyle = "#ffffff";
    previewCtx.fillRect(0, 0, previewCanvas.width, previewCanvas.height);
  }

  function renderRegionsOnlyPreview() {
    if (!previewCtx || !previewCanvas) return;
    clearPreviewCanvas();
    for (var i = 0; i < regions.length; i += 1) {
      var region = regions[i];
      if (!region.points || region.points.length < 2) continue;
      previewCtx.save();
      previewCtx.beginPath();
      previewCtx.moveTo(region.points[0].x, region.points[0].y);
      for (var p = 1; p < region.points.length; p += 1) {
        previewCtx.lineTo(region.points[p].x, region.points[p].y);
      }
      previewCtx.closePath();
      previewCtx.fillStyle = "#000000";
      previewCtx.fill();
      previewCtx.restore();
    }
  }

  function getBoundsFromPoints(points) {
    var minX = points[0].x;
    var minY = points[0].y;
    var maxX = points[0].x;
    var maxY = points[0].y;
    for (var i = 1; i < points.length; i += 1) {
      var point = points[i];
      if (point.x < minX) minX = point.x;
      if (point.y < minY) minY = point.y;
      if (point.x > maxX) maxX = point.x;
      if (point.y > maxY) maxY = point.y;
    }
    return {
      x: Math.round(minX),
      y: Math.round(minY),
      width: Math.round(maxX - minX),
      height: Math.round(maxY - minY),
      x2: Math.round(maxX),
      y2: Math.round(maxY)
    };
  }

  function regionToJson(region) {
    var points = region.points.map(function (point) {
      return { x: Math.round(point.x), y: Math.round(point.y) };
    });
    var bounds = getBoundsFromPoints(region.points);
    return {
      id: region.id,
      points: points,
      bounds: bounds
    };
  }

  function syncRegionsJson() {
    if (!regionsJsonEl) return;
    var normalized = regions.map(regionToJson);
    regionsJsonEl.textContent = JSON.stringify(normalized, null, 2);
  }

  function clamp(value, min, max) {
    if (value < min) return min;
    if (value > max) return max;
    return value;
  }

  function distance(a, b) {
    var dx = a.x - b.x;
    var dy = a.y - b.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  function getCanvasPos(event) {
    var rect = canvas.getBoundingClientRect();
    var scaleX = canvas.width / rect.width;
    var scaleY = canvas.height / rect.height;
    return {
      x: clamp((event.clientX - rect.left) * scaleX, 0, canvas.width),
      y: clamp((event.clientY - rect.top) * scaleY, 0, canvas.height)
    };
  }

  async function importImage(file) {
    if (!isAllowedImage(file)) {
      setStatus("Format harus JPG, PNG, atau BMP.", "error");
      return;
    }
    setStatus("Memproses gambar ke 512x512...", "default");
    try {
      var dataUrl = await readDataUrl(file);
      var image = await loadImage(dataUrl);
      pushHistory();
      backgroundImage = image;
      regions = [];
      regionSeq = 1;
      draftPoints = [];
      syncRegionsJson();
      renderCanvas();
      setStatus("Gambar berhasil ditampilkan di canvas 512x512. Silakan free drawing region.", "success");
    } catch (error) {
      setStatus("Gagal memproses gambar.", "error");
    }
  }

  importBtn.addEventListener("click", function () {
    importFile.click();
  });

  importFile.addEventListener("change", function () {
    var file = importFile.files && importFile.files[0] ? importFile.files[0] : null;
    importFile.value = "";
    if (!file) return;
    importImage(file);
  });

  clearBtn.addEventListener("click", function () {
    pushHistory();
    backgroundImage = null;
    regions = [];
    regionSeq = 1;
    draftPoints = [];
    drawing = false;
    syncRegionsJson();
    renderCanvas();
    setStatus("Canvas dibersihkan.", "default");
  });

  clearRegionsBtn.addEventListener("click", function () {
    pushHistory();
    regions = [];
    regionSeq = 1;
    draftPoints = [];
    drawing = false;
    syncRegionsJson();
    renderCanvas();
    setStatus("Semua region dihapus.", "default");
  });

  downloadBtn.addEventListener("click", function () {
    var link = document.createElement("a");
    link.href = canvas.toDataURL("image/png");
    link.download = "canvas-mode2-512.png";
    link.click();
  });

  copyJsonBtn.addEventListener("click", function () {
    if (!navigator.clipboard) {
      setStatus("Clipboard tidak tersedia di browser ini.", "error");
      return;
    }
    navigator.clipboard.writeText(regionsJsonEl.textContent || "[]").then(
      function () {
        setStatus("JSON region berhasil disalin.", "success");
      },
      function () {
        setStatus("Gagal menyalin JSON region.", "error");
      }
    );
  });

  if (previewBtn) {
    previewBtn.addEventListener("click", function () {
      previewEnabled = true;
      renderRegionsOnlyPreview();
      setStatus("Preview mask region berhasil digenerate.", "success");
    });
  }

  if (previewDownloadBtn) {
    previewDownloadBtn.addEventListener("click", function () {
      if (!previewCanvas) {
        setStatus("Preview canvas tidak tersedia.", "error");
        return;
      }
      previewEnabled = true;
      renderRegionsOnlyPreview();
      var link = document.createElement("a");
      link.href = previewCanvas.toDataURL("image/png");
      link.download = "canvas-mode2-region-mask-512.png";
      link.click();
      setStatus("Preview PNG region mask berhasil diunduh.", "success");
    });
  }

  undoBtn.addEventListener("click", function () {
    if (history.length === 0) {
      setStatus("Belum ada aksi yang bisa di-undo.", "default");
      return;
    }
    var snapshot = history.pop();
    restoreFromSnapshot(snapshot);
    setStatus("Undo berhasil.", "success");
  });

  canvas.addEventListener("mousedown", function (event) {
    if (!backgroundImage) {
      setStatus("Import gambar dulu sebelum menggambar region.", "error");
      return;
    }
    if (event.button !== 0) return;
    drawing = true;
    var pos = getCanvasPos(event);
    draftPoints = [{ x: pos.x, y: pos.y }];
    renderCanvas();
  });

  canvas.addEventListener("mousemove", function (event) {
    if (!drawing) return;
    var pos = getCanvasPos(event);
    if (draftPoints.length === 0 || distance(draftPoints[draftPoints.length - 1], pos) >= 1.5) {
      draftPoints.push({ x: pos.x, y: pos.y });
    }
    renderCanvas();
  });

  function finishDrawing() {
    if (!drawing) return;
    drawing = false;
    if (draftPoints.length >= 3) {
      var startPoint = draftPoints[0];
      var endPoint = draftPoints[draftPoints.length - 1];
      if (distance(startPoint, endPoint) > 1.5) {
        draftPoints.push({ x: startPoint.x, y: startPoint.y });
      }
      pushHistory();
      regions.push({
        id: regionSeq,
        points: draftPoints.slice()
      });
      regionSeq += 1;
      syncRegionsJson();
      setStatus("Free drawing region ditambahkan.", "success");
    }
    draftPoints = [];
    renderCanvas();
  }

  canvas.addEventListener("mouseup", finishDrawing);
  canvas.addEventListener("mouseleave", finishDrawing);

  syncRegionsJson();
  renderCanvas();
  clearPreviewCanvas();
})();
