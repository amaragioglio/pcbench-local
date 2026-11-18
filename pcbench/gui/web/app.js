"use strict";

// PCBench Local window. All data comes from Python through window.pywebview.api.

const state = { lang: "es", strings: {}, tab: "security", view: { state: "empty" }, progress: null, steps: [], polling: null };
const $ = (id) => document.getElementById(id);

const PREVIEW = [
  { key: "pv_av", step: "security" }, { key: "pv_fw", step: "security" },
  { key: "pv_upd", step: "security" }, { key: "pv_acc", step: "security" },
  { key: "pv_remote", step: "security" }, { key: "pv_boot", step: "security" },
  { key: "pv_cpu", step: "cpu" }, { key: "pv_ram", step: "memory" },
  { key: "pv_disk", step: "disk" }, { key: "pv_net", step: "network" },
];

function t(key, values) {
  const table = state.strings[state.lang] || {};
  let text = table[key] ?? (state.strings.en || {})[key] ?? key;
  if (values) for (const [k, v] of Object.entries(values)) text = text.replace(`{${k}}`, v);
  return text;
}

function applyStaticText() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-t]").forEach((el) => { el.textContent = t(el.dataset.t); });
  document.querySelectorAll(".lang button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === state.lang)));
}

function formatDate(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  const text = date.toLocaleString(state.lang === "es" ? "es" : "en", { dateStyle: "long", timeStyle: "short" });
  return t("done_at", { date: text });
}

// ---------- rendering ----------
function render() {
  applyStaticText();
  const view = state.view || { state: "empty" };
  const running = state.progress && state.progress.phase === "running";
  const done = view.state === "done";

  const run = $("run");
  run.disabled = running;
  run.textContent = running ? t("running") : done ? t("run_again") : t("run");

  $("progress").hidden = !running;
  if (running) {
    $("progress-label").textContent = state.progress.label || "";
    const pct = Math.max(4, Math.round(((state.progress.step - 1) / state.progress.total) * 100));
    $("progress-fill").style.width = `${pct}%`;
  }

  $("tally").hidden = !done;
  $("report").hidden = !done || running;
  $("tabs").hidden = !done || running;
  $("date").textContent = done ? formatDate(view.finished_at) : "";

  const verdict = $("verdict");
  verdict.className = "verdict";
  if (done && !running) {
    verdict.classList.add(view.verdict.level);
    $("verdict-title").textContent = view.verdict.title;
    $("verdict-sub").textContent = view.partial ? `${view.verdict.subtitle} ${t("partial_note")}` : view.verdict.subtitle;
    $("t-red").textContent = view.tally.red;
    $("t-amber").textContent = view.tally.amber;
    $("t-green").textContent = view.tally.green;
    $("t-red-label").textContent = view.tally.red === 1 ? t("urgent") : t("urgent_plural");
    setCount("c-security", view.tally.red, view.tally.amber);
    const perfLines = view.performance[0].lines.filter((l) => l.id !== "perf_score");
    const perfRed = perfLines.filter((l) => l.light === "red").length;
    const perfAmber = perfLines.filter((l) => l.light === "amber").length;
    setCount("c-performance", perfRed, perfAmber);
  } else {
    $("verdict-title").textContent = running ? t("running_title") : t("never_checked");
    $("verdict-sub").textContent = running ? "" : t("intro");
  }

  $("tab-security").setAttribute("aria-selected", String(state.tab === "security"));
  $("tab-performance").setAttribute("aria-selected", String(state.tab === "performance"));

  const panel = $("panel");
  panel.replaceChildren();
  if (done && !running) {
    const groups = state.tab === "security" ? view.security : view.performance;
    groups.forEach((group, gi) => panel.append(renderGroup(group, gi)));
  } else {
    panel.append(renderPreview(running));
  }
}

function setCount(id, red, amber) {
  const el = $(id);
  const n = red + amber;
  el.textContent = n ? String(n) : "";
  el.className = `count ${red ? "red" : amber ? "amber" : ""}`;
}

let stampIndex = 0;
function renderGroup(group, gi) {
  const section = document.createElement("section");
  section.className = "group";
  const title = document.createElement("h2");
  title.className = "group-title";
  title.textContent = group.group;
  const list = document.createElement("ul");
  list.className = "lines";
  if (gi === 0) stampIndex = 0;
  group.lines.forEach((line) => list.append(renderRow(line)));
  section.append(title, list);
  return section;
}

function lightLabel(light) {
  return { red: t("urgent"), amber: t("attention"), green: t("fine"), note: t("note"), grey: t("failed") }[light] || "";
}

function renderRow(line) {
  const row = document.getElementById("row-tpl").content.firstElementChild.cloneNode(true);
  row.dataset.light = line.light;
  if (state.justFinished) {
    row.classList.add("stamp");
    row.style.setProperty("--i", String(stampIndex++));
  }
  row.querySelector(".lights").setAttribute("aria-label", lightLabel(line.light));
  const title = row.querySelector(".row-title");
  title.textContent = line.title;
  if (line.resolved || line.light === "note") {
    const tag = document.createElement("span");
    tag.className = line.resolved ? "tag resolved" : "tag";
    tag.textContent = line.resolved ? t("resolved") : t("note");
    title.append(tag);
  }
  row.querySelector(".row-detail").textContent = line.detail || "";
  row.querySelector(".row-value").textContent = line.value || "";

  const head = row.querySelector(".row-head");
  const body = row.querySelector(".row-body");
  const hasBody = Boolean(line.why || (line.fix && line.fix.length));
  if (!hasBody || line.resolved) {
    row.classList.add("static");
    head.removeAttribute("aria-expanded");
    head.tabIndex = -1;
  } else {
    row.querySelector(".why").textContent = line.why || "";
    const fix = row.querySelector(".fix");
    (line.fix || []).forEach((step) => { const li = document.createElement("li"); li.textContent = step; fix.append(li); });
    if (!line.fix || !line.fix.length) row.querySelector(".fix-title").hidden = true;
    row.querySelector(".fix-title").textContent = t("how_to_fix");
    const open = line.light === "red";
    head.setAttribute("aria-expanded", String(open));
    body.hidden = !open;
    head.addEventListener("click", () => {
      const expanded = head.getAttribute("aria-expanded") === "true";
      head.setAttribute("aria-expanded", String(!expanded));
      body.hidden = expanded;
    });
  }
  return row;
}

function renderPreview(running) {
  const frag = document.createDocumentFragment();
  const title = document.createElement("h2");
  title.className = "preview-title";
  title.textContent = t("preview_title");
  const list = document.createElement("ul");
  list.className = "lines";
  const current = running ? state.progress.name : null;
  const order = state.steps;
  PREVIEW.forEach((item) => {
    const row = document.getElementById("row-tpl").content.firstElementChild.cloneNode(true);
    row.classList.add("static");
    row.dataset.light = "off";
    row.querySelector(".row-title").textContent = t(item.key);
    const detail = row.querySelector(".row-detail");
    if (running) {
      const finished = order.indexOf(item.step) < order.indexOf(current);
      if (item.step === current) { row.classList.add("checking"); detail.textContent = t("checking"); }
      else if (!finished) detail.textContent = t("pending");
    }
    row.querySelector(".row-head").tabIndex = -1;
    list.append(row);
  });
  frag.append(title, list);
  return frag;
}

// ---------- actions ----------
async function refresh() {
  const status = await window.pywebview.api.status();
  const wasRunning = state.progress && state.progress.phase === "running";
  state.progress = status.progress;
  state.view = status.view;
  state.justFinished = wasRunning && status.progress.phase === "done";
  render();
  state.justFinished = false;
  if (status.progress.phase !== "running" && state.polling) { clearInterval(state.polling); state.polling = null; }
}

async function start() {
  await window.pywebview.api.start_scan();
  $("saved").hidden = true;
  await refresh();
  if (!state.polling) state.polling = setInterval(refresh, 450);
}

async function boot() {
  const info = await window.pywebview.api.init();
  state.lang = info.language;
  state.strings = info.strings;
  state.steps = info.steps;
  const admin = $("admin");
  admin.hidden = false;
  admin.textContent = info.is_admin ? t("admin_yes") : t("admin_no");
  admin.dataset.key = info.is_admin ? "admin_yes" : "admin_no";
  admin.classList.toggle("no", !info.is_admin);
  $("elevate").hidden = info.is_admin || !info.can_elevate;

  $("run").addEventListener("click", start);
  $("tab-security").addEventListener("click", () => { state.tab = "security"; render(); });
  $("tab-performance").addEventListener("click", () => { state.tab = "performance"; render(); });
  $("tabs").addEventListener("keydown", (e) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    state.tab = state.tab === "security" ? "performance" : "security";
    render();
    $(`tab-${state.tab}`).focus();
  });
  document.querySelectorAll(".lang button").forEach((b) => b.addEventListener("click", async () => {
    state.lang = b.dataset.lang;
    const status = await window.pywebview.api.set_language(state.lang);
    state.view = status.view;
    admin.textContent = t(admin.dataset.key);
    render();
  }));
  $("save").addEventListener("click", async () => {
    const result = await window.pywebview.api.save_report($("hide").checked);
    $("saved").hidden = !result.ok;
  });
  $("folder").addEventListener("click", () => window.pywebview.api.open_reports_folder());
  $("elevate").addEventListener("click", () => window.pywebview.api.restart_as_admin());
  await refresh();
}

if (window.pywebview && window.pywebview.api) boot();
else window.addEventListener("pywebviewready", boot);
