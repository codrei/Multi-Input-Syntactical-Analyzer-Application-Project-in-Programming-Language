/* SyntaxLens web app.
 *
 * The page does not analyze code itself.  It sends the code to the server
 * (POST api/analyze), which runs the same Python analyzer as the command line,
 * and shows the JSON reply:
 *   - a PASSED / FAILED banner, counts and two bar charts,
 *   - tabs: Errors (with a pointer to the column and a fix), Line Breakdown,
 *     Tokens, and the text Report (detailed or classic, copy or download).
 * Errors are also marked inside the code editor: a red line, a dot in the
 * margin and a wavy underline under the exact token.
 */
"use strict";

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const MAX_BYTES = 2 * 1024 * 1024;
const CHECK_LABELS = [
  "Brackets", "Strings & chars", "Terminators", "Operators",
  "Control headers", "Identifiers", "Indentation & blocks", "Illegal characters",
];

const state = {
  mode: "line",            // which input tab is open: "line", "block" or "file"
  result: null,            // the last reply from the server
  reportStyle: "detailed",
  tokenFilter: "all",
  file: null,              // the chosen file: {name, size, base64}
  marks: [],               // editor decorations to remove before the next analysis
  samples: [],
};

/* Build an element: h("p", {class: "x"}, "text", child).  Text is always set
   with textContent, so code and messages are shown, never run as HTML. */
function h(tag, attributes = {}, ...children) {
  const element = document.createElement(tag);
  for (const [key, value] of Object.entries(attributes)) {
    if (value === false || value == null) continue;
    if (key.startsWith("on")) element.addEventListener(key.slice(2), value);
    else element.setAttribute(key, value === true ? "" : value);
  }
  for (const child of children.flat()) {
    if (child != null) element.append(child instanceof Node ? child : String(child));
  }
  return element;
}

const plural = (count, word) => `${count} ${word}${count === 1 ? "" : "s"}`;

/* ------------------------------------------------------------------ editors */

const blockEditor = CodeMirror.fromTextArea($("#block-code"), {
  lineNumbers: true,
  mode: "python",
  indentUnit: 4,
  tabSize: 4,
  matchBrackets: true,
  styleActiveLine: true,
  gutters: ["sl-markers", "CodeMirror-linenumbers"],
  placeholder: "Paste or type several lines of code here, or load a sample above...",
  extraKeys: {
    "Ctrl-Enter": () => analyze(),
    "Cmd-Enter": () => analyze(),
    Tab: (cm) => cm.replaceSelection("    "),
  },
});
let fileViewer = null; // created the first time a file is shown

function editorFor(mode) {
  return mode === "block" ? blockEditor : mode === "file" ? fileViewer : null;
}

function syntaxMode(language) {
  return language === "java" ? "text/x-java" : "python";
}

function guessMode(filename) {
  return /\.java$/i.test(filename || "") ? "text/x-java" : "python";
}

/* --------------------------------------------------------------------- tabs */

function setupTabs(listLabel, onSelect) {
  const tabs = $$(`[aria-label="${listLabel}"] [role="tab"]`);
  function select(tab) {
    for (const other of tabs) {
      const selected = other === tab;
      other.setAttribute("aria-selected", String(selected));
      other.tabIndex = selected ? 0 : -1;
      document.getElementById(other.getAttribute("aria-controls")).hidden = !selected;
    }
    onSelect(tab);
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => select(tab));
    tab.addEventListener("keydown", (event) => {
      const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
      if (!step) return;
      const next = tabs[(index + step + tabs.length) % tabs.length];
      next.focus();
      select(next);
    });
  });
  return (name, attribute) => select(tabs.find((tab) => tab.dataset[attribute] === name));
}

const selectInputTab = setupTabs("Input mode", (tab) => {
  state.mode = tab.dataset.mode;
  if (state.mode === "block") blockEditor.refresh();
  if (state.mode === "file" && fileViewer) fileViewer.refresh();
  if (state.mode === "line") $("#line-code").focus();
});
const selectResultTab = setupTabs("Result views", () => {});

/* ----------------------------------------------------------------- analysis */

async function analyze() {
  const payload = buildRequest();
  if (!payload) return;
  setBusy(true);
  showRequestError(null);
  try {
    const response = await fetch("api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json().catch(() => ({ error: "The server sent an unreadable reply." }));
    if (!response.ok) throw new Error(data.error || `The request failed (${response.status}).`);
    state.result = data;
    render(data);
  } catch (error) {
    const offline = error instanceof TypeError;   // fetch() itself failed
    showRequestError(offline ? "Could not reach the SyntaxLens server. Is it still running?" : error.message);
  } finally {
    setBusy(false);
  }
}

function buildRequest() {
  const language = $("#language").value;
  if (state.mode === "line") {
    const code = $("#line-code").value;
    if (!code.trim()) return showRequestError("Type a line of code first.");
    return { mode: "line", code, language };
  }
  if (state.mode === "block") {
    const code = blockEditor.getValue();
    if (!code.trim()) return showRequestError("Type or paste some code first.");
    return { mode: "block", code, language };
  }
  if (!state.file) return showRequestError("Choose a file first.");
  return { mode: "file", filename: state.file.name, content_base64: state.file.base64, language };
}

function setBusy(busy) {
  for (const button of $$("[data-analyze]")) {
    button.disabled = busy;
    button.textContent = busy ? "Analyzing..." : "Analyze";
  }
}

function showRequestError(message) {
  const box = $("#request-error");
  box.hidden = !message;
  box.textContent = message || "";
  return null;
}

/* ------------------------------------------------------------------- render */

function render(data) {
  $("#empty-state").hidden = true;
  $("#results").hidden = false;
  $("#timing").textContent = `Analyzed in ${data.summary.elapsed_ms} ms`;
  renderStatus(data);
  renderStats(data);
  renderCharts(data);
  renderErrors(data);
  renderLines(data);
  renderTokens(data);
  renderReport();
  if (data.mode === "file") showFile(data);
  markEditor(data);
}

function renderStatus(data) {
  const passed = data.status === "PASSED";
  const { errors, warnings } = data.summary;
  const headline = passed
    ? `PASSED - no syntax errors${warnings ? `, ${plural(warnings, "warning")}` : ""}`
    : `FAILED - ${plural(errors, "syntax error")} detected`;
  const icon = passed
    ? '<svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    : '<svg viewBox="0 0 24 24"><path d="M7 7l10 10M17 7L7 17" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>';
  const box = $("#status");
  box.className = `status ${passed ? "passed" : "failed"}`;
  const iconBox = h("div", { class: "icon" });
  iconBox.innerHTML = icon; // fixed markup above, never user content
  box.replaceChildren(iconBox, h("div", {},
    h("strong", {}, headline),
    h("span", {}, `${data.language.description} · ${plural(data.source.lines, "line")} · source: ${data.source.name}`),
  ));
}

function renderStats(data) {
  const s = data.summary;
  const stat = (value, label, tone) => h("div", { class: `stat ${tone || ""}` }, h("b", {}, value), h("span", {}, label));
  $("#stats").replaceChildren(
    stat(s.errors, "syntax errors", s.errors ? "bad" : "good"),
    stat(s.warnings, "warnings", s.warnings ? "warn" : ""),
    stat(`${s.valid_lines} / ${s.total_lines}`, "valid lines", s.flagged_lines.length ? "" : "good"),
    stat(s.total_tokens, "tokens parsed"),
  );
  const errorCount = $("#count-errors");
  errorCount.textContent = s.errors + s.warnings;
  errorCount.className = `count ${s.errors ? "bad" : ""}`;
  $("#count-tokens").textContent = s.total_tokens;
}

function barRow(label, title, value, max, tone) {
  const width = max ? Math.round((value / max) * 100) : 0;
  return h("div", { class: `bar-row ${value ? "" : "zero"}`, title },
    h("span", { class: "label" }, label),
    h("span", { class: "track" }, h("span", { class: `fill ${tone}`, style: `width:${width}%` })),
    h("span", { class: "value" }, value),
  );
}

function renderCharts(data) {
  const checks = data.errors_by_check;
  const checkMax = Math.max(1, ...checks.map((c) => c.errors + c.warnings));
  $("#chart-checks").replaceChildren(...checks.map((c, i) => barRow(
    `${c.check}. ${CHECK_LABELS[i]}`,
    `${c.title}: ${plural(c.errors, "error")}, ${plural(c.warnings, "warning")}`,
    c.errors + c.warnings, checkMax, c.errors ? "bad" : "warn",
  )));
  const tokens = data.tokens_by_category;
  const tokenMax = Math.max(1, ...tokens.map((t) => t.count));
  $("#chart-tokens").replaceChildren(...tokens.map((t) => barRow(
    t.category,
    `${t.category}: ${Object.keys(t.items).slice(0, 12).join("  ")}`,
    t.count, tokenMax, "tok",
  )));
}

function numbered(diagnostics) {
  let errors = 0;
  let warnings = 0;
  return diagnostics.map((d) => ({
    ...d,
    label: d.severity === "error" ? `ERROR ${++errors}` : `WARNING ${++warnings}`,
  }));
}

function pointerText(d) {
  // The code line with a caret under the column (tabs expanded to 4 spaces).
  let visual = 0;
  for (const char of d.code_line.slice(0, d.column - 1)) visual += char === "\t" ? 4 - (visual % 4) : 1;
  const gutter = String(d.line);
  return [`${gutter} | ${d.code_line.replace(/\t/g, "    ")}`, `${" ".repeat(gutter.length)} | ${" ".repeat(visual)}`];
}

function renderErrors(data) {
  const pane = $("#rpane-errors");
  if (!data.diagnostics.length) {
    pane.replaceChildren(h("div", { class: "all-clear" },
      `No syntax errors found. All ${plural(data.source.lines, "line")} passed the 8 checks.`));
    return;
  }
  const cards = numbered(data.diagnostics).map((d) => {
    const [codeLine, caretLine] = pointerText(d);
    return h("article", {
      class: `card ${d.severity}`, tabindex: 0,
      title: "Show this line in the code",
      onclick: () => focusLine(d.line, d.column),
      onkeydown: (event) => { if (event.key === "Enter") focusLine(d.line, d.column); },
    },
      h("div", { class: "card-head" },
        h("span", { class: "badge" }, d.code),
        h("strong", {}, `[${d.label}] Line ${d.line}, column ${d.column}`),
        h("span", { class: "muted" }, `Check ${d.check}: ${d.check_title}`),
      ),
      h("h4", {}, d.category),
      h("p", {}, d.message),
      h("pre", { class: "snippet" }, `${codeLine}\n${caretLine}`, h("span", { class: "caret" }, "^")),
      d.hint ? h("p", { class: "fix" }, d.hint) : null,
    );
  });
  pane.replaceChildren(h("div", { class: "cards" }, cards));
}

function renderLines(data) {
  const labels = new Map(numbered(data.diagnostics).map((d) => [`${d.line}:${d.code}:${d.column}`, d.label]));
  const head = h("tr", {}, ["Line", "Code", "Statement", "Check", "Delimiters"].map((t) => h("th", {}, t)));
  const rows = data.lines.filter((line) => line.status !== "blank").map((line) => {
    const refs = data.diagnostics.filter((d) => d.line === line.number)
      .map((d) => labels.get(`${d.line}:${d.code}:${d.column}`));
    const pill = line.status === "ok" ? h("span", { class: "pill ok" }, "OK")
      : h("span", { class: `pill ${line.status}` }, `${line.status.toUpperCase()} (${refs.join(", ")})`);
    return h("tr", { class: line.status === "ok" ? "" : line.status },
      h("td", {}, line.number),
      h("td", { class: "code" }, line.text.trim()),
      h("td", {}, line.label),
      h("td", {}, pill),
      h("td", {}, line.delimiters),
    );
  });
  $("#lines-table").replaceChildren(h("thead", {}, head), h("tbody", {}, rows));
}

function renderTokens(data) {
  // One filter button per token category; each token carries its category's key.
  const filters = [{ key: "all", label: "All", count: data.tokens.length }]
    .concat(data.tokens_by_category.map((t) => ({ key: t.key, label: t.category, count: t.count })));
  if (!filters.some((f) => f.key === state.tokenFilter)) state.tokenFilter = "all";
  $("#token-filters").replaceChildren(...filters.map((f) => h("button", {
    class: "chip", type: "button", "aria-pressed": String(state.tokenFilter === f.key),
    disabled: f.count === 0 && f.key !== "all",
    onclick: () => { state.tokenFilter = f.key; renderTokens(data); },
  }, `${f.label} (${f.count})`)));

  const shown = data.tokens
    .map((token, index) => ({ ...token, number: index + 1 }))
    .filter((token) => state.tokenFilter === "all" || token.category_key === state.tokenFilter);
  const limit = 3000;
  const head = h("tr", {}, ["#", "Line:Col", "Category", "Token", "Note"].map((t) => h("th", {}, t)));
  const rows = shown.slice(0, limit).map((token) => h("tr", { class: token.issue ? "error" : "" },
    h("td", {}, token.number),
    h("td", {}, `${token.line}:${token.column}`),
    h("td", {}, token.category),
    h("td", { class: "code" }, token.text.length > 60 ? `${token.text.slice(0, 57)}...` : token.text),
    h("td", {}, token.issue || ""),
  ));
  if (shown.length > limit) {
    rows.push(h("tr", {}, h("td", { colspan: 5 }, `... and ${shown.length - limit} more tokens (see the Report tab)`)));
  }
  $("#tokens-table").replaceChildren(h("thead", {}, head), h("tbody", {}, rows));
}

function renderReport() {
  if (!state.result) return;
  $("#report-text").textContent = state.result.report[state.reportStyle];
  for (const button of $$(".segmented button")) {
    button.setAttribute("aria-pressed", String(button.dataset.style === state.reportStyle));
  }
}

/* ------------------------------------------------------- editor highlights */

function clearMarks() {
  for (const mark of state.marks) mark.clear();
  state.marks = [];
}

function markEditor(data) {
  clearMarks();
  const cm = editorFor(data.mode);
  if (!cm) return;
  cm.setOption("mode", syntaxMode(data.language.key));
  for (const d of data.diagnostics) {
    const line = d.line - 1;
    if (line >= cm.lineCount()) continue;
    const kind = d.severity === "error" ? "error" : "warning";
    const tip = `${d.code}: ${d.message}${d.hint ? `\nFix: ${d.hint}` : ""}`;
    cm.addLineClass(line, "background", `sl-line-${kind}`);
    state.marks.push({ clear: () => cm.removeLineClass(line, "background", `sl-line-${kind}`) });
    const dot = h("span", { class: `sl-marker ${kind}`, title: tip });
    cm.setGutterMarker(line, "sl-markers", dot);
    state.marks.push({ clear: () => cm.setGutterMarker(line, "sl-markers", null) });
    const token = data.tokens.find((t) => t.line === d.line && t.column === d.column);
    const length = token && token.end_line === token.line ? token.end_column - token.column : 1;
    const from = { line, ch: d.column - 1 };
    const to = { line, ch: Math.min(d.column - 1 + Math.max(length, 1), cm.getLine(line).length || 1) };
    if (to.ch <= from.ch) from.ch = Math.max(0, to.ch - 1);
    state.marks.push(cm.markText(from, to, { className: `sl-underline-${kind}`, attributes: { title: tip } }));
  }
}

function focusLine(line, column) {
  const cm = editorFor(state.result && state.result.mode);
  if (cm && state.mode === state.result.mode) {
    const position = { line: line - 1, ch: Math.max(column - 1, 0) };
    cm.focus();
    cm.setCursor(position);
    cm.scrollIntoView(position, 120);
    cm.addLineClass(line - 1, "wrap", "sl-line-focus");
    setTimeout(() => cm.removeLineClass(line - 1, "wrap", "sl-line-focus"), 1500);
  } else if (state.mode === "line") {
    const input = $("#line-code");
    input.focus();
    input.setSelectionRange(column - 1, column);
  }
}

/* ---------------------------------------------------------------- the file */

function readFile(file) {
  if (!file) return;
  if (file.size > MAX_BYTES) {
    showRequestError(`${file.name} is ${(file.size / 1048576).toFixed(1)} MB; the limit is 2 MB.`);
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    state.file = { name: file.name, size: file.size, base64: toBase64(new Uint8Array(reader.result)) };
    $("#file-info").hidden = false;
    $("#file-info").replaceChildren(
      h("span", {}, h("strong", {}, file.name), h("span", { class: "muted" }, `  ${formatSize(file.size)}`)),
      h("button", { class: "button primary", type: "button", onclick: () => analyze() }, "Analyze again"),
    );
    analyze();
  };
  reader.onerror = () => showRequestError("The file could not be read.");
  reader.readAsArrayBuffer(file);
}

function toBase64(bytes) {
  let binary = "";
  for (let i = 0; i < bytes.length; i += 0x8000) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  }
  return btoa(binary);
}

function formatSize(bytes) {
  return bytes < 1024 ? `${bytes} bytes` : `${(bytes / 1024).toFixed(1)} KB`;
}

function showFile(data) {
  const view = $("#file-view");
  view.hidden = false;
  if (!fileViewer) {
    fileViewer = CodeMirror(view, {
      readOnly: true, lineNumbers: true, tabSize: 4, matchBrackets: true,
      gutters: ["sl-markers", "CodeMirror-linenumbers"],
    });
  }
  fileViewer.setValue(data.lines.map((line) => line.text).join("\n"));
  fileViewer.setOption("mode", syntaxMode(data.language.key));
  fileViewer.refresh();
}

/* ------------------------------------------------------------------ actions */

function download(text, filename, type) {
  const link = h("a", { href: URL.createObjectURL(new Blob([text], { type })), download: filename });
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}

function reportName(extension) {
  const name = state.result ? state.result.source.name.replace(/[<>]/g, "").replace(/\s+/g, "-") : "report";
  return `syntaxlens-${name.replace(/\.[^.]+$/, "") || "report"}.${extension}`;
}

function wireEvents() {
  for (const button of $$("[data-analyze]")) button.addEventListener("click", () => analyze());
  $("#line-code").addEventListener("keydown", (event) => { if (event.key === "Enter") analyze(); });
  for (const chip of $$("[data-example]")) {
    chip.addEventListener("click", () => { $("#line-code").value = chip.dataset.example; analyze(); });
  }

  let timer = null;
  blockEditor.on("change", () => {
    if (state.result && state.result.mode === "block") clearMarks(); // old marks no longer fit the text
    if (!$("#live").checked) return;
    clearTimeout(timer);
    timer = setTimeout(() => { if (blockEditor.getValue().trim()) analyze(); }, 600);
  });
  $("#clear-block").addEventListener("click", () => { blockEditor.setValue(""); blockEditor.focus(); });
  $("#sample-select").addEventListener("change", (event) => {
    const sample = state.samples.find((s) => s.id === event.target.value);
    if (sample) loadSample(sample);
    event.target.value = "";
  });

  const zone = $("#drop-zone");
  zone.addEventListener("dragover", (event) => { event.preventDefault(); zone.classList.add("dragging"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("dragging"));
  zone.addEventListener("drop", (event) => {
    event.preventDefault();
    zone.classList.remove("dragging");
    readFile(event.dataTransfer.files[0]);
  });
  $("#file-input").addEventListener("change", (event) => { readFile(event.target.files[0]); event.target.value = ""; });

  for (const button of $$(".segmented button")) {
    button.addEventListener("click", () => { state.reportStyle = button.dataset.style; renderReport(); });
  }
  $("#copy-report").addEventListener("click", async () => {
    const button = $("#copy-report");
    try {
      await navigator.clipboard.writeText($("#report-text").textContent);
      button.textContent = "Copied!";
    } catch (error) {
      button.textContent = "Copy failed";
    }
    setTimeout(() => { button.textContent = "Copy"; }, 1500);
  });
  $("#download-txt").addEventListener("click", () =>
    download($("#report-text").textContent, reportName("txt"), "text/plain;charset=utf-8"));
  $("#download-json").addEventListener("click", () => {
    const { report, ...data } = state.result;
    download(JSON.stringify(data, null, 2), reportName("json"), "application/json");
  });

  $("#theme-toggle").addEventListener("click", () => {
    const dark = document.documentElement.dataset.theme !== "dark";
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    try { localStorage.setItem("syntaxlens-theme", dark ? "dark" : "light"); } catch (error) { /* private mode */ }
  });
}

function loadSample(sample) {
  selectInputTab("block", "mode");
  blockEditor.setOption("mode", guessMode(sample.filename));
  blockEditor.setValue(sample.code.replace(/\n$/, ""));
  return analyze();
}

/* -------------------------------------------------------------------- start */

async function start() {
  wireEvents();
  try {
    const [info, samples] = await Promise.all([
      fetch("api/info").then((r) => r.json()),
      fetch("api/samples").then((r) => r.json()),
    ]);
    $("#version").textContent = `v${info.version}`;
    for (const language of info.languages) {
      $("#language").append(h("option", { value: language.key }, language.name));
    }
    state.samples = samples.samples;
    for (const sample of state.samples) {
      $("#sample-select").append(h("option", { value: sample.id }, sample.title));
    }
  } catch (error) {
    showRequestError("Could not reach the SyntaxLens server. Is it still running?");
    return;
  }
  // Links can open the page ready to show something, for demos and screenshots:
  //   #sample=spec_example_2        load a sample into the Code Block tab and analyze it
  //   #line=y%20%3D%2020%20%2B%20*%205   analyze one line in the Single Line tab
  //   &view=lines|tokens|report     then open that results tab
  const params = new URLSearchParams(location.hash.slice(1));
  const sample = state.samples.find((s) => s.id === params.get("sample"));
  if (params.get("line")) {
    $("#line-code").value = params.get("line");
    await analyze();
  } else if (sample) {
    await loadSample(sample);
  }
  if (params.get("view") && state.result) selectResultTab(params.get("view"), "view");
}

start();
