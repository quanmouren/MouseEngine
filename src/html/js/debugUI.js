(function () {
    "use strict";

    // 刷新间隔
    var REFRESH_MS = 50;

    var monitorGrid = document.getElementById("monitorGrid");
    var realtimePanel = document.getElementById("realtime");
    var decisionPanel = document.getElementById("decision");
    var windowListPanel = document.getElementById("windowList");
    var fpsEl = document.getElementById("fps");

    var pywebviewReady = false;
    var frameCount = 0;
    var fpsWindowStart = performance.now();
    var thumbImages = {};

    function esc(text) {
        var div = document.createElement("div");
        div.textContent = text == null ? "" : String(text);
        return div.innerHTML;
    }

    function short(text, n) {
        text = text == null ? "" : String(text);
        return text.length > n ? text.slice(0, n - 1) + "…" : text;
    }

    function timeText(ts) {
        if (!ts) return "更新中…";
        var d = new Date(ts * 1000);
        function p(n) { return (n < 10 ? "0" : "") + n; }
        return p(d.getHours()) + ":" + p(d.getMinutes()) + ":" + p(d.getSeconds());
    }

    function waitForPywebview() {
        if (window.pywebview && window.pywebview.api) {
            pywebviewReady = true;
            start();
            return;
        }
        window.addEventListener("pywebviewready", function () {
            if (!pywebviewReady) {
                pywebviewReady = true;
                start();
            }
        });
        setTimeout(function () {
            if (!pywebviewReady) {
                realtimePanel.innerHTML = '<div class="error">pywebview 未就绪，无法获取调试数据</div>';
            }
        }, 3000);
    }

    function start() {
        poll();
        setInterval(poll, REFRESH_MS);
    }

    async function poll() {
        if (!pywebviewReady) return;
        try {
            var snap = await window.pywebview.api.get_snapshot();
            render(snap);
            frameCount += 1;
            updateFps();
        } catch (e) {
            console.error("debug 轮询失败:", e);
        }
    }

    function updateFps() {
        var now = performance.now();
        var elapsed = now - fpsWindowStart;
        if (elapsed >= 1000) {
            var fps = Math.round((frameCount * 1000) / elapsed);
            fpsEl.textContent = fps + " FPS / " + REFRESH_MS + "ms";
            frameCount = 0;
            fpsWindowStart = now;
        }
    }

    function render(snap) {
        renderLayout(snap);
        renderMonitors(snap.monitors || [], snap.realtime || {});
        renderRealtime(snap.realtime || {});
        renderDecision(snap.decision || {});
        renderWindows(snap.windows || []);
    }

    function rectText(rect) {
        if (!rect || rect.length !== 4) return "";
        return (rect[2] - rect[0]) + "x" + (rect[3] - rect[1]);
    }

    function renderMonitors(monitors, realtime) {
        var mouseDevice = realtime.mouse_monitor ? realtime.mouse_monitor.device_name : null;
        if (!monitors.length) {
            monitorGrid.innerHTML = '<div class="empty">未检测到显示器</div>';
            return;
        }
        monitorGrid.innerHTML = monitors.map(function (m) {
            var isCurrent = mouseDevice && m.device_name === mouseDevice;
            var primary = m.primary ? '<span class="badge badge-primary">主屏</span>' : "";
            var current = isCurrent ? '<span class="badge badge-current">鼠标在此</span>' : "";
            var thumb = m.thumbnail
                ? '<img class="thumb" src="' + esc(m.thumbnail) + '" alt="壁纸">'
                : '<div class="thumb thumb-empty">无缩略图</div>';
            var wp = m.wallpaper_id
                ? '<div class="wp-id">壁纸 ID: ' + esc(m.wallpaper_id) + '</div>'
                : '<div class="wp-id wp-none">未绑定壁纸</div>';
            var bindLine = m.mouse_group
                ? '<div class="group-id">绑定组: ' + esc(m.mouse_group) + '</div>'
                : '<div class="group-id group-none">绑定组: 未绑定</div>';
            var effLine = m.effective_group
                ? '<div class="group-eff">生效组: ' + esc(m.effective_group) + ' <span class="group-src">' + esc(m.effective_source || "") + '</span></div>'
                : '<div class="group-eff group-none">生效组: 无</div>';
            return (
                '<div class="monitor-card' + (isCurrent ? " is-current" : "") + '">' +
                    thumb +
                    '<div class="monitor-info">' +
                        '<div class="monitor-title">M' + m.visual_no + ' · ' + esc(m.device_name) + '</div>' +
                        '<div class="monitor-name">' + esc(m.display_name || "") + '</div>' +
                        '<div class="monitor-badges">' + primary + current + '</div>' +
                        '<div class="monitor-meta">' + rectText(m.rect) + ' · DPI ' + m.dpi_x + '</div>' +
                        wp +
                        '<div class="wp-source">来源: ' + esc(m.wallpaper_source || "-") + '</div>' +
                        bindLine +
                        effLine +
                    '</div>' +
                '</div>'
            );
        }).join("");
    }

    function renderRealtime(realtime) {
        var mouse = realtime.mouse ? realtime.mouse[0] + ", " + realtime.mouse[1] : "未获取";
        var mm = realtime.mouse_monitor
            ? realtime.mouse_monitor.visual_no + "号屏 (" + realtime.mouse_monitor.device_name + ")"
            : "未识别";
        var mw = windowLine(realtime.mouse_window, "未识别");
        var fw = windowLine(realtime.foreground_window, "未识别");
        realtimePanel.innerHTML =
            '<div class="rt-grid">' +
                kv("鼠标坐标", mouse) +
                kv("鼠标所在显示器", mm) +
            '</div>' +
            '<div class="rt-window">' +
                '<div class="rt-row"><span class="rt-label">前台窗口</span><span class="rt-value">' + fw + '</span></div>' +
                '<div class="rt-row"><span class="rt-label">鼠标命中窗口</span><span class="rt-value">' + mw + '</span></div>' +
            '</div>';
    }

    function windowLine(w, fallback) {
        if (!w) return fallback;
        return esc(w.title || "(空标题)") + " [" + esc(w.class_name) + "] pid=" + w.pid;
    }

    function kv(label, value) {
        return '<div class="rt-row"><span class="rt-label">' + esc(label) + '</span><span class="rt-value">' + esc(value) + '</span></div>';
    }

    function renderDecision(decision) {
        if (!decisionPanel) return;
        if (!decision || !decision.nodes || !decision.nodes.length) {
            decisionPanel.innerHTML = '<div class="empty">无决策数据</div>';
            return;
        }
        var mon = decision.monitor || {};
        var header = "";
        if (mon.device_name) {
            header =
                '<div class="dc-header">' +
                    '<div class="dc-title">当前状态</div>' +
                    '<div>鼠标: M' + mon.visual_no + ' (' + esc(mon.device_name) + ')</div>' +
                    (mon.wallpaper_id ? '<div>壁纸: ' + esc(mon.wallpaper_id) + '</div>' : '<div>壁纸: 无</div>') +
                    '<div>前台: ' + esc(decision.foreground_process || "无") + '</div>' +
                    '<div class="dc-meta">数据源: ' + esc(decision.wallpaper_reader || "DLL") + ' · ' + timeText(decision.fetched_at) + '</div>' +
                '</div>';
        }
        var nodes = decision.nodes.map(function (n) {
            var unknown = n.status === "unknown" ? '<span class="dc-badge-unknown">未知</span>' : "";
            var yesCls = n.yes.taken ? "dc-branch dc-branch-taken" : "dc-branch";
            var noCls = n.no.taken ? "dc-branch dc-branch-taken" : "dc-branch";
            return (
                '<div class="dc-node">' +
                    '<div class="dc-node-head">' +
                        '<span class="dc-node-name">' + esc(n.name) + '</span>' + unknown +
                    '</div>' +
                    '<div class="dc-cond">' + esc(n.condition || "") + '</div>' +
                    '<div class="' + yesCls + '"><span class="dc-branch-key">是</span><span class="dc-branch-label">' + esc(n.yes.label || "") + '</span></div>' +
                    '<div class="' + noCls + '"><span class="dc-branch-key">否</span><span class="dc-branch-label">' + esc(n.no.label || "") + '</span></div>' +
                '</div>'
            );
        }).join('<div class="dc-connector">→</div>');

        var finalCls = decision.final_group ? "dc-final" : "dc-final dc-final-none";
        var finalText = decision.final_group
            ? '<div class="dc-final-title">最终生效</div><div class="dc-final-group">「' + esc(decision.final_group) + '」</div>'
            : '<div class="dc-final-title">最终</div><div class="dc-final-group">不应用</div>';
        var final = '<div class="' + finalCls + '">' + finalText + '<div class="dc-final-src">' + esc(decision.final_source || "") + '</div></div>';

        decisionPanel.innerHTML = header + nodes + final;
    }

    function renderWindows(windows) {
        if (!windows.length) {
            windowListPanel.innerHTML = '<div class="empty">无可见窗口</div>';
            return;
        }
        windowListPanel.innerHTML = windows.slice(0, 60).map(function (w) {
            return (
                '<div class="window-item">' +
                    '<span class="w-z">W' + w.z_no + '</span>' +
                    '<span class="w-title">' + esc(w.title) + '</span>' +
                    '<span class="w-class">' + esc(w.class_name) + '</span>' +
                    '<span class="w-pid">pid ' + w.pid + '</span>' +
                    '<span class="w-rect">' + rectText(w.rect) + '</span>' +
                '</div>'
            );
        }).join("");
    }


    function getThumbImage(path) {
        if (!path) return null;
        if (!thumbImages[path]) {
            var img = new Image();
            img.src = path;
            thumbImages[path] = img;
        }
        return thumbImages[path];
    }

    function prepareTransform(w, h, vr) {
        var vx1 = vr[0], vy1 = vr[1], vx2 = vr[2], vy2 = vr[3];
        var virtualW = Math.max(vx2 - vx1, 1);
        var virtualH = Math.max(vy2 - vy1, 1);
        var margin = 56;
        var scale = Math.max(0.01, Math.min((w - margin * 2) / virtualW, (h - margin * 2) / virtualH));
        return {
            vx1: vx1, vy1: vy1, vx2: vx2, vy2: vy2,
            scale: scale,
            offsetX: (w - virtualW * scale) / 2,
            offsetY: (h - virtualH * scale) / 2
        };
    }

    function cx(t, x) { return t.offsetX + (x - t.vx1) * t.scale; }
    function cy(t, y) { return t.offsetY + (y - t.vy1) * t.scale; }
    function rectToCanvas(t, r) {
        return [cx(t, r[0]), cy(t, r[1]), cx(t, r[2]), cy(t, r[3])];
    }

    function renderLayout(snap) {
        var canvas = document.getElementById("layoutCanvas");
        if (!canvas) return;
        var wrap = canvas.parentElement;
        var w = wrap.clientWidth;
        var h = wrap.clientHeight;
        if (w < 10 || h < 10) return;
        var dpr = window.devicePixelRatio || 1;
        if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
            canvas.width = Math.round(w * dpr);
            canvas.height = Math.round(h * dpr);
        }
        canvas.style.width = w + "px";
        canvas.style.height = h + "px";
        var ctx = canvas.getContext("2d");
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.clearRect(0, 0, w, h);
        ctx.fillStyle = "#0b1220";
        ctx.fillRect(0, 0, w, h);

        var monitors = snap.monitors || [];
        if (!monitors.length) {
            ctx.fillStyle = "#64748b";
            ctx.font = "12px Segoe UI";
            ctx.textAlign = "center";
            ctx.fillText("没有检测到显示器", w / 2, h / 2);
            return;
        }

        var t = prepareTransform(w, h, snap.virtual_rect || [0, 0, 0, 0]);
        drawGrid(ctx, t);
        drawVirtualScreen(ctx, t);
        drawMonitors(ctx, t, monitors, snap.realtime || {});
        drawWindows(ctx, t, snap.windows || []);
        drawHighlights(ctx, t, snap.realtime || {});
        drawMousePoint(ctx, t, snap.realtime || {});
        drawLegend(ctx, w);
    }

    function drawGrid(ctx, t) {
        var step = 500;
        var startX = Math.floor(t.vx1 / step) * step;
        var endX = Math.ceil(t.vx2 / step) * step;
        var startY = Math.floor(t.vy1 / step) * step;
        var endY = Math.ceil(t.vy2 / step) * step;
        ctx.strokeStyle = "#1e293b";
        ctx.fillStyle = "#64748b";
        ctx.font = "9px Consolas";
        ctx.lineWidth = 1;
        ctx.setLineDash([2, 4]);
        for (var x = startX; x <= endX; x += step) {
            var gx = cx(t, x);
            ctx.beginPath();
            ctx.moveTo(gx, cy(t, t.vy1));
            ctx.lineTo(gx, cy(t, t.vy2));
            ctx.stroke();
            ctx.fillText(String(x), gx + 4, cy(t, t.vy1) + 14);
        }
        for (var y = startY; y <= endY; y += step) {
            var gy = cy(t, y);
            ctx.beginPath();
            ctx.moveTo(cx(t, t.vx1), gy);
            ctx.lineTo(cx(t, t.vx2), gy);
            ctx.stroke();
            ctx.fillText(String(y), cx(t, t.vx1) + 4, gy - 4);
        }
        ctx.setLineDash([]);
        if (t.vx1 <= 0 && 0 <= t.vx2 && t.vy1 <= 0 && 0 <= t.vy2) {
            var ox = cx(t, 0), oy = cy(t, 0);
            ctx.strokeStyle = "#ef4444";
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(ox, cy(t, t.vy1));
            ctx.lineTo(ox, cy(t, t.vy2));
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(cx(t, t.vx1), oy);
            ctx.lineTo(cx(t, t.vx2), oy);
            ctx.stroke();
            ctx.fillStyle = "#ef4444";
            ctx.beginPath();
            ctx.arc(ox, oy, 4, 0, Math.PI * 2);
            ctx.fill();
            ctx.textAlign = "left";
            ctx.fillText("0,0", ox + 8, oy + 14);
        }
    }

    function drawVirtualScreen(ctx, t) {
        var r = rectToCanvas(t, [t.vx1, t.vy1, t.vx2, t.vy2]);
        ctx.strokeStyle = "#475569";
        ctx.lineWidth = 2;
        ctx.setLineDash([]);
        ctx.strokeRect(r[0], r[1], r[2] - r[0], r[3] - r[1]);
        ctx.fillStyle = "#94a3b8";
        ctx.font = "bold 10px Consolas";
        ctx.textAlign = "left";
        ctx.fillText(
            "Virtual Desktop: (" + t.vx1 + ", " + t.vy1 + ") - (" + t.vx2 + ", " + t.vy2 + ")  " + (t.vx2 - t.vx1) + "x" + (t.vy2 - t.vy1),
            r[0], r[1] - 8
        );
    }

    function drawMonitors(ctx, t, monitors, realtime) {
        var currentHmon = realtime.mouse_monitor ? realtime.mouse_monitor.hmonitor : null;
        monitors.forEach(function (m) {
            var r = rectToCanvas(t, m.rect);
            var w = r[2] - r[0], h = r[3] - r[1];
            var isCurrent = currentHmon != null && m.hmonitor === currentHmon;

            var fill = m.primary ? "#16283f" : "#1e293b";
            var outline = m.primary ? "#60a5fa" : "#475569";
            var lw = 2;
            if (isCurrent) { fill = "#3a2a05"; outline = "#f59e0b"; lw = 4; }

            ctx.fillStyle = fill;
            ctx.fillRect(r[0], r[1], w, h);

            if (m.thumbnail) {
                var img = getThumbImage(m.thumbnail);
                if (img && img.complete && img.naturalWidth) {
                    ctx.save();
                    ctx.beginPath();
                    ctx.rect(r[0], r[1], w, h);
                    ctx.clip();
                    var sw = img.naturalWidth, sh = img.naturalHeight;
                    var s = Math.max(w / sw, h / sh);
                    var dw = sw * s, dh = sh * s;
                    ctx.drawImage(img, r[0] + (w - dw) / 2, r[1] + (h - dh) / 2, dw, dh);
                    ctx.fillStyle = "rgba(2, 6, 23, 0.45)";
                    ctx.fillRect(r[0], r[1], w, h);
                    ctx.restore();
                }
            }

            ctx.strokeStyle = outline;
            ctx.lineWidth = lw;
            ctx.setLineDash([]);
            ctx.strokeRect(r[0], r[1], w, h);

            var wr = rectToCanvas(t, m.work_rect);
            ctx.strokeStyle = "#22c55e";
            ctx.lineWidth = 1;
            ctx.setLineDash([5, 3]);
            ctx.strokeRect(wr[0], wr[1], wr[2] - wr[0], wr[3] - wr[1]);
            ctx.setLineDash([]);

            var mx = (r[0] + r[2]) / 2;
            var my = (r[1] + r[3]) / 2;
            ctx.textAlign = "center";
            ctx.fillStyle = "#ffffff";
            ctx.font = "bold 14px Consolas";
            var title = "M" + m.visual_no;
            if (m.primary) title += " / PRIMARY";
            if (isCurrent) title += " / MOUSE HERE";
            ctx.fillText(title, mx, my - 16);

            ctx.fillStyle = "#e2e8f0";
            ctx.font = "10px Consolas";
            ctx.fillText((m.rect[2] - m.rect[0]) + "x" + (m.rect[3] - m.rect[1]) + "  DPI " + m.dpi_x, mx, my + 2);
            ctx.fillText(m.device_name, mx, my + 16);

            ctx.textAlign = "left";
            ctx.fillStyle = "#cbd5e1";
            ctx.font = "9px Consolas";
            ctx.fillText("(" + m.rect[0] + ", " + m.rect[1] + ")", r[0] + 6, r[3] - 8);
            if (m.wallpaper_id) {
                ctx.textAlign = "right";
                ctx.fillStyle = "#38bdf8";
                ctx.fillText("ID " + m.wallpaper_id, r[2] - 6, r[3] - 8);
            }
        });
    }

    function drawWindows(ctx, t, windows) {
        windows.slice().reverse().forEach(function (w) {
            var r = rectToCanvas(t, w.rect);
            var ww = r[2] - r[0], wh = r[3] - r[1];
            ctx.strokeStyle = "#fb923c";
            ctx.lineWidth = 1.5;
            ctx.setLineDash([4, 2]);
            ctx.strokeRect(r[0], r[1], ww, wh);
            ctx.setLineDash([]);
            if (ww > 70 && wh > 30) {
                var label = "W" + w.z_no + " " + short(w.title, 22);
                ctx.fillStyle = "rgba(67, 20, 7, 0.9)";
                ctx.fillRect(r[0], r[1], Math.min(ww, label.length * 7 + 12), 18);
                ctx.fillStyle = "#fdba74";
                ctx.font = "9px Consolas";
                ctx.textAlign = "left";
                ctx.fillText(label, r[0] + 4, r[1] + 12);
            }
        });
    }

    function drawHighlights(ctx, t, realtime) {
        if (realtime.foreground_window) {
            var r = rectToCanvas(t, realtime.foreground_window.rect);
            ctx.strokeStyle = "#a78bfa";
            ctx.lineWidth = 3;
            ctx.setLineDash([]);
            ctx.strokeRect(r[0], r[1], r[2] - r[0], r[3] - r[1]);
            ctx.fillStyle = "#a78bfa";
            ctx.font = "bold 10px Consolas";
            ctx.textAlign = "left";
            ctx.fillText("FOCUS: " + short(realtime.foreground_window.title || realtime.foreground_window.class_name, 28), r[0] + 6, r[1] - 8);
        }
        if (realtime.mouse_window) {
            var r2 = rectToCanvas(t, realtime.mouse_window.rect);
            ctx.strokeStyle = "#ef4444";
            ctx.lineWidth = 3;
            ctx.setLineDash([]);
            ctx.strokeRect(r2[0], r2[1], r2[2] - r2[0], r2[3] - r2[1]);
            ctx.fillStyle = "#ef4444";
            ctx.font = "bold 10px Consolas";
            ctx.textAlign = "left";
            ctx.fillText("UNDER MOUSE: " + short(realtime.mouse_window.title || realtime.mouse_window.class_name, 28), r2[0] + 6, r2[3] + 12);
        }
    }

    function drawMousePoint(ctx, t, realtime) {
        if (!realtime.mouse) return;
        var px = cx(t, realtime.mouse[0]);
        var py = cy(t, realtime.mouse[1]);
        ctx.strokeStyle = "#0f172a";
        ctx.lineWidth = 3;
        ctx.setLineDash([]);
        ctx.beginPath();
        ctx.moveTo(px - 10, py);
        ctx.lineTo(px + 10, py);
        ctx.moveTo(px, py - 10);
        ctx.lineTo(px, py + 10);
        ctx.stroke();
        ctx.fillStyle = "#ef4444";
        ctx.beginPath();
        ctx.arc(px, py, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.fillStyle = "#e2e8f0";
        ctx.font = "bold 9px Consolas";
        ctx.textAlign = "left";
        ctx.fillText("Mouse (" + realtime.mouse[0] + ", " + realtime.mouse[1] + ")", px + 12, py + 16);
    }

    function drawLegend(ctx, w) {
        ctx.fillStyle = "#94a3b8";
        ctx.font = "10px Microsoft YaHei UI";
        ctx.textAlign = "center";
        ctx.fillText("橙色虚线=窗口 · 黄色=鼠标所在显示器 · 紫色=焦点窗口 · 红色=鼠标命中窗口 · 红点=鼠标位置", w / 2, 12);
    }

    waitForPywebview();
})();
