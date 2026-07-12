const totalExamples = document.querySelector("#totalExamples");
const passRate = document.querySelector("#passRate");
const reviewCount = document.querySelector("#reviewCount");
const p95Latency = document.querySelector("#p95Latency");
const dimensionTable = document.querySelector("#dimensionTable");
const metricDetail = document.querySelector("#metricDetail");
const refreshEval = document.querySelector("#refreshEval");
const metricsText = document.querySelector("#metricsText");
const tracePanel = document.querySelector("#tracePanel");
const insightList = document.querySelector("#insightList");
const reviewList = document.querySelector("#reviewList");

let qualityMetrics = [];
let selectedMetricName = null;

function pct(value) {
  return `${Math.round(Number(value) * 100)}%`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  }[char]));
}

function withoutTerminalPeriod(value) {
  return String(value).replace(/\.(?=\s*$)/, "");
}

function readableName(value) {
  return String(value).replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

function renderMetricDetail(metric) {
  if (!metric) {
    metricDetail.innerHTML = `<p class="empty-copy">No metric selected</p>`;
    return;
  }
  metricDetail.innerHTML = `
    <div class="metric-detail-status ${metric.passed ? "pass" : "review"}">${metric.passed ? "Gate passed" : "Review required"}</div>
    <p class="section-kicker">Definition</p>
    <h3>${escapeHtml(metric.label)}</h3>
    <div class="metric-detail-score"><strong>${pct(metric.value)}</strong><span>threshold ${pct(metric.threshold)}</span></div>
    <p>${escapeHtml(withoutTerminalPeriod(metric.explanation))}</p>
    <div class="formula-block"><span>Equation</span><div class="formula-equation" aria-label="${escapeHtml(withoutTerminalPeriod(metric.formula))}"></div><div class="formula-notation" aria-label="${escapeHtml(withoutTerminalPeriod(metric.formula_notation))}"></div></div>
  `;
  const formulaElement = metricDetail.querySelector(".formula-equation");
  if (window.katex && metric.formula_latex) {
    window.katex.render(metric.formula_latex, formulaElement, { displayMode: true, throwOnError: false, strict: false });
  } else {
    formulaElement.textContent = withoutTerminalPeriod(metric.formula);
    formulaElement.classList.add("formula-fallback");
  }

  const notationElement = metricDetail.querySelector(".formula-notation");
  const notationFragments = metric.formula_notation_latex || [];
  if (window.katex && notationFragments.length) {
    notationFragments.forEach((fragment) => {
      const term = document.createElement("span");
      term.className = "notation-term";
      notationElement.appendChild(term);
      window.katex.render(fragment, term, { displayMode: false, throwOnError: false, strict: false });
    });
  } else {
    notationElement.textContent = withoutTerminalPeriod(metric.formula_notation);
  }
}

function selectMetric(name) {
  selectedMetricName = name;
  document.querySelectorAll(".metric-row").forEach((row) => {
    const selected = row.dataset.metric === name;
    row.classList.toggle("selected", selected);
    row.setAttribute("aria-selected", String(selected));
  });
  renderMetricDetail(qualityMetrics.find((metric) => metric.name === name));
}

function renderMetricTable(metrics) {
  qualityMetrics = metrics;
  if (!metrics.length) {
    dimensionTable.innerHTML = `<p class="empty-copy">No metrics returned</p>`;
    renderMetricDetail(null);
    return;
  }
  dimensionTable.innerHTML = metrics.map((metric) => `
    <button class="metric-row ${metric.passed ? "pass" : "review"}" type="button" data-metric="${escapeHtml(metric.name)}" aria-selected="false">
      <span class="metric-name"><i aria-hidden="true"></i><strong>${escapeHtml(metric.label)}</strong></span>
      <span class="metric-score">${pct(metric.value)}</span>
      <span class="metric-gate">${pct(metric.threshold)}</span>
      <span class="metric-track"><i style="width: ${Math.round(metric.value * 100)}%"></i><b style="left: ${Math.round(metric.threshold * 100)}%"></b></span>
    </button>
  `).join("");
  dimensionTable.querySelectorAll(".metric-row").forEach((row) => {
    row.addEventListener("click", () => selectMetric(row.dataset.metric));
  });
  selectMetric(selectedMetricName && metrics.some((metric) => metric.name === selectedMetricName) ? selectedMetricName : metrics[0].name);
}

function renderInsights(insights) {
  insightList.innerHTML = insights.length ? insights.map((insight) => `
    <article class="insight-row ${escapeHtml(insight.severity)}">
      <div><span class="severity-label">${escapeHtml(insight.severity)}</span><strong>${escapeHtml(readableName(insight.dimension))}</strong></div>
      <p>${escapeHtml(withoutTerminalPeriod(insight.finding))}</p>
      <small>${escapeHtml(withoutTerminalPeriod(insight.recommendation))}</small>
    </article>
  `).join("") : `<p class="empty-copy">No failed gates</p>`;
}

function weakestMetric(record) {
  const entries = Object.entries(record.metric_scores || {});
  if (!entries.length) return ["overall", 0];
  return entries.sort((left, right) => left[1] - right[1])[0];
}

function renderReviewQueue(records) {
  const reviewRecords = records.filter((record) => record.requires_review).slice(0, 8);
  reviewList.innerHTML = reviewRecords.length ? reviewRecords.map((record) => {
    const [metric, score] = weakestMetric(record);
    return `
      <article class="review-row">
        <header><strong>${escapeHtml(record.example_id)}</strong><span>${escapeHtml(record.category)}</span></header>
        <p>${escapeHtml(record.query)}</p>
        <footer><span>${escapeHtml(readableName(metric))}: ${pct(score)}</span><span>${escapeHtml(record.expected_action)} / ${escapeHtml(record.predicted_action)}</span></footer>
      </article>
    `;
  }).join("") : `<p class="empty-copy">No records flagged</p>`;
}

async function loadEvaluation() {
  refreshEval.disabled = true;
  refreshEval.textContent = "Running";
  try {
    const response = await fetch("/evaluation/report");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const report = await response.json();
    totalExamples.textContent = report.summary.total_examples;
    passRate.textContent = pct(report.summary.pass_rate);
    reviewCount.textContent = report.summary.review_count;
    p95Latency.textContent = `${report.summary.latency_p95_ms.toFixed(2)} ms`;
    renderMetricTable(report.summary.quality_metrics || []);
    renderInsights(report.insights || []);
    renderReviewQueue(report.records || []);
  } catch (error) {
    dimensionTable.innerHTML = `<p class="inline-error">Evaluation report unavailable: ${escapeHtml(String(error))}</p>`;
    metricDetail.innerHTML = `<p class="empty-copy">Definitions could not be loaded</p>`;
    insightList.innerHTML = `<p class="empty-copy">Recommendations unavailable</p>`;
    reviewList.innerHTML = `<p class="empty-copy">Review queue unavailable</p>`;
  } finally {
    refreshEval.disabled = false;
    refreshEval.textContent = "Run again";
  }
}

async function loadMetrics() {
  try {
    const response = await fetch("/metrics");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    metricsText.textContent = await response.text();
  } catch (error) {
    metricsText.textContent = `# Metrics unavailable\n# ${String(error)}`;
  }
}

async function loadTrace() {
  try {
    const response = await fetch("/trace/latest");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const trace = await response.json();
    if (!trace.query) {
      tracePanel.innerHTML = `<p class="empty-copy">No query recorded</p>`;
      return;
    }
    const checks = Object.entries(trace.quality_checks || {});
    tracePanel.innerHTML = `
      <div class="trace-row"><span>Query</span><p>${escapeHtml(trace.query)}</p></div>
      <div class="trace-row split"><div><span>Provider</span><strong>${escapeHtml(trace.provider)}</strong></div><div><span>Latency</span><strong>${Number(trace.latency_ms).toFixed(2)} ms</strong></div></div>
      <div class="trace-row"><span>Retrieved chunks</span><p class="mono-copy">${trace.retrieved_docs.map((document) => `${escapeHtml(document.doc_id)} [${Number(document.score).toFixed(3)}]`).join("\n")}</p></div>
      <div class="trace-row"><span>Live checks</span><div class="trace-checks">${checks.map(([name, passed]) => `<small class="${passed ? "pass" : "review"}">${escapeHtml(readableName(name))}</small>`).join("")}</div></div>
    `;
  } catch (error) {
    tracePanel.innerHTML = `<p class="inline-error">Trace unavailable: ${escapeHtml(String(error))}</p>`;
  }
}

refreshEval.addEventListener("click", async () => {
  await Promise.all([loadEvaluation(), loadMetrics(), loadTrace()]);
});

loadEvaluation();
loadMetrics();
loadTrace();
setInterval(loadMetrics, 5000);
setInterval(loadTrace, 5000);
