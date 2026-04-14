/**
 * Dashboard: function points + COCOMO with debounced API calls and Chart.js.
 */

const API = {
  calculateFp: "/api/calculate-fp/",
  calculateCocomo: "/api/calculate-cocomo/",
  projects: "/api/projects/",
  exportPdf: (id) => `/api/export-pdf/${id}/`,
  meta: "/api/meta/",
};

const FP_TYPES = [
  { key: "ei", label: "External Inputs (EI)", weights: [3, 4, 6] },
  { key: "eo", label: "External Outputs (EO)", weights: [4, 5, 7] },
  { key: "eq", label: "External Inquiries (EQ)", weights: [3, 4, 6] },
  { key: "ilf", label: "Internal Logical Files (ILF)", weights: [7, 10, 15] },
  { key: "eif", label: "External Interface Files (EIF)", weights: [5, 7, 10] },
];

const DEBOUNCE_MS = 280;

let gscFactors = [];
let debounceTimer = null;
let chartFp = null;
let chartEffort = null;
/** @type {number | null} */
let lastSavedProjectId = null;

function debounce(fn) {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(fn, DEBOUNCE_MS);
}

function readCounts() {
  const out = {};
  for (const t of FP_TYPES) {
    out[t.key] = {
      simple: Number(document.getElementById(`cnt-${t.key}-s`).value) || 0,
      average: Number(document.getElementById(`cnt-${t.key}-a`).value) || 0,
      complex: Number(document.getElementById(`cnt-${t.key}-c`).value) || 0,
    };
  }
  return out;
}

function readGsc() {
  const n = gscFactors.length || 14;
  const values = [];
  for (let i = 0; i < n; i += 1) {
    const el = document.getElementById(`gsc-${i}`);
    values.push(el ? Number(el.value) : 3);
  }
  return values;
}

function buildFpPayload() {
  const c = readCounts();
  return {
    ei: c.ei,
    eo: c.eo,
    eq: c.eq,
    ilf: c.ilf,
    eif: c.eif,
    gsc: readGsc(),
  };
}

function renderFpTable() {
  const tbody = document.getElementById("fp-rows");
  tbody.innerHTML = "";
  for (const t of FP_TYPES) {
    const tr = document.createElement("tr");
    const w = t.weights.join(" / ");
    tr.innerHTML = `
      <th scope="row" class="type-label">${t.label}</th>
      <td><input type="number" min="0" step="1" id="cnt-${t.key}-s" value="0" aria-label="${t.label} simple count" /></td>
      <td><input type="number" min="0" step="1" id="cnt-${t.key}-a" value="0" aria-label="${t.label} average count" /></td>
      <td><input type="number" min="0" step="1" id="cnt-${t.key}-c" value="0" aria-label="${t.label} complex count" /></td>
      <td class="num weight-hint">${w}</td>
    `;
    tbody.appendChild(tr);
  }
  tbody.querySelectorAll("input").forEach((el) => {
    el.addEventListener("input", () => debounce(recalculate));
  });
}

function renderGscSliders(factors) {
  gscFactors = factors;
  const root = document.getElementById("gsc-sliders");
  root.innerHTML = "";
  factors.forEach((f, i) => {
    const div = document.createElement("div");
    div.className = "gsc-item";
    div.innerHTML = `
      <label for="gsc-${i}">
        <span class="gsc-name">${f.label}</span>
        <span class="gsc-val" id="gsc-val-${i}">3</span>
      </label>
      <input type="range" id="gsc-${i}" min="0" max="5" step="1" value="3" aria-valuemin="0" aria-valuemax="5" />
    `;
    root.appendChild(div);
  });
  factors.forEach((_, i) => {
    const range = document.getElementById(`gsc-${i}`);
    const val = document.getElementById(`gsc-val-${i}`);
    range.addEventListener("input", () => {
      val.textContent = range.value;
      debounce(recalculate);
    });
  });
}

function setStatus(text, isError = false) {
  const el = document.getElementById("result-status");
  el.textContent = text;
  el.classList.toggle("error-text", isError);
}

function formatNum(v, digits = 4) {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return Number(v).toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: 0,
  });
}

async function postJson(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg =
      (data && (data.detail || (Array.isArray(data) ? JSON.stringify(data) : null))) ||
      res.statusText;
    throw new Error(typeof msg === "string" ? msg : "Request failed");
  }
  return data;
}

function ensureCharts() {
  if (typeof Chart === "undefined") return;

  const fpCtx = document.getElementById("chart-fp");
  const efCtx = document.getElementById("chart-effort");

  if (!chartFp) {
    chartFp = new Chart(fpCtx, {
      type: "doughnut",
      data: {
        labels: [],
        datasets: [
          {
            data: [],
            backgroundColor: ["#5eead4", "#a78bfa", "#fbbf24", "#fb7185", "#38bdf8"],
            borderWidth: 0,
          },
        ],
      },
      options: {
        plugins: { legend: { position: "bottom", labels: { color: "#e8edf5" } } },
        maintainAspectRatio: false,
      },
    });
  }
  if (!chartEffort) {
    chartEffort = new Chart(efCtx, {
      type: "bar",
      data: {
        labels: ["Effort (PM)", "TDEV (months)"],
        datasets: [
          {
            label: "Estimate",
            data: [0, 0],
            backgroundColor: ["#5eead4", "#a78bfa"],
            borderRadius: 8,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { ticks: { color: "#9aa7b8" }, grid: { color: "rgba(255,255,255,0.06)" } },
          y: {
            beginAtZero: true,
            ticks: { color: "#9aa7b8" },
            grid: { color: "rgba(255,255,255,0.06)" },
          },
        },
        plugins: { legend: { display: false } },
      },
    });
  }
}

function updateFpChart(breakdown) {
  ensureCharts();
  if (!chartFp || !breakdown) return;
  const labels = Object.keys(breakdown);
  const data = labels.map((k) => breakdown[k]);
  chartFp.data.labels = labels;
  chartFp.data.datasets[0].data = data;
  chartFp.update();
}

function updateEffortChart(effort, tdev) {
  ensureCharts();
  if (!chartEffort) return;
  chartEffort.data.datasets[0].data = [effort, tdev];
  chartEffort.update();
}

async function recalculate() {
  setStatus("Calculating…");
  try {
    const payload = buildFpPayload();
    const fpRes = await postJson(API.calculateFp, payload);
    const mode = document.getElementById("cocomo-mode").value;
    const coco = await postJson(API.calculateCocomo, { fp: fpRes.fp, mode });

    document.getElementById("metric-ufp").textContent = formatNum(fpRes.ufp);
    document.getElementById("metric-caf").textContent = formatNum(fpRes.caf);
    document.getElementById("metric-fp").textContent = formatNum(fpRes.fp);
    document.getElementById("metric-kloc").textContent = formatNum(coco.kloc, 6);
    document.getElementById("metric-effort").textContent = formatNum(coco.effort_pm);
    document.getElementById("metric-tdev").textContent = formatNum(coco.tdev_months);

    updateFpChart(fpRes.ufp_breakdown);
    updateEffortChart(coco.effort_pm, coco.tdev_months);
    setStatus("Up to date.");
  } catch (e) {
    setStatus(e.message || "Calculation failed", true);
  }
}

async function loadMeta() {
  const res = await fetch(API.meta);
  if (!res.ok) throw new Error("Failed to load metadata");
  return res.json();
}

function updateDownloadReportButton() {
  const btn = document.getElementById("btn-download-report");
  const hint = document.getElementById("download-hint");
  const hasId = lastSavedProjectId != null;
  btn.disabled = !hasId;
  btn.title = hasId ? "Download PDF for the last saved snapshot" : "Save an estimate first";
  hint.style.display = hasId ? "none" : "";
}

function parseFilenameFromContentDisposition(header) {
  if (!header) return null;
  const utf8 = /filename\*=UTF-8''([^;]+)/i.exec(header);
  if (utf8) return decodeURIComponent(utf8[1]);
  const plain = /filename="([^"]+)"/i.exec(header) || /filename=([^;]+)/i.exec(header);
  if (plain) return plain[1].trim().replace(/^"|"$/g, "");
  return null;
}

async function downloadProjectPdf(projectId) {
  const res = await fetch(API.exportPdf(projectId));
  if (res.status === 404) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Project not found.");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || res.statusText || "Download failed");
  }
  const blob = await res.blob();
  const filename =
    parseFilenameFromContentDisposition(res.headers.get("Content-Disposition")) ||
    `estimate-${projectId}.pdf`;
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function loadHistory() {
  const res = await fetch(API.projects);
  if (!res.ok) return;
  const rows = await res.json();
  const tbody = document.getElementById("history-body");
  tbody.innerHTML = "";
  for (const r of rows) {
    const tr = document.createElement("tr");
    const d = new Date(r.updated_at);
    tr.innerHTML = `
      <td>${escapeHtml(r.name)}</td>
      <td class="num">${formatNum(r.fp)}</td>
      <td class="num">${formatNum(r.effort_pm)}</td>
      <td class="num">${formatNum(r.tdev_months)}</td>
      <td>${d.toLocaleString()}</td>
      <td class="actions-col"><button type="button" class="btn btn-ghost" data-pdf-id="${r.id}">PDF</button></td>
    `;
    tbody.appendChild(tr);
  }
  tbody.querySelectorAll("[data-pdf-id]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = Number(btn.getAttribute("data-pdf-id"));
      try {
        await downloadProjectPdf(id);
      } catch (e) {
        const msg = document.getElementById("save-msg");
        msg.textContent = e.message || "PDF download failed";
        msg.classList.add("error-text");
      }
    });
  });
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function saveProject() {
  const nameInput = document.getElementById("project-name");
  const msg = document.getElementById("save-msg");
  const name = nameInput.value.trim();
  if (!name) {
    msg.textContent = "Enter a project name.";
    msg.classList.add("error-text");
    return;
  }
  msg.textContent = "Saving…";
  msg.classList.remove("error-text");
  try {
    const body = {
      name,
      ...buildFpPayload(),
      cocomo_mode: document.getElementById("cocomo-mode").value,
    };
    const created = await postJson(API.projects, body);
    if (created && created.id != null) {
      lastSavedProjectId = Number(created.id);
      updateDownloadReportButton();
    }
    msg.textContent = "Saved.";
    nameInput.value = "";
    await loadHistory();
  } catch (e) {
    msg.textContent = e.message || "Save failed";
    msg.classList.add("error-text");
  }
}

async function init() {
  renderFpTable();
  try {
    const meta = await loadMeta();
    renderGscSliders(meta.factors);
  } catch {
    const fallback = Array.from({ length: 14 }, (_, id) => ({
      id,
      label: `GSC ${id + 1}`,
    }));
    renderGscSliders(fallback);
  }

  document.getElementById("cocomo-mode").addEventListener("change", () => debounce(recalculate));
  document.getElementById("btn-save").addEventListener("click", saveProject);
  document.getElementById("btn-download-report").addEventListener("click", async () => {
    if (lastSavedProjectId == null) return;
    const msg = document.getElementById("save-msg");
    msg.classList.remove("error-text");
    try {
      await downloadProjectPdf(lastSavedProjectId);
      msg.textContent = "Report downloaded.";
    } catch (e) {
      msg.textContent = e.message || "PDF download failed";
      msg.classList.add("error-text");
    }
  });

  updateDownloadReportButton();
  await loadHistory();
  await recalculate();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
