const runtime = document.querySelector("#homeRuntime");

function setRuntime(status, label, detail = "") {
  runtime.className = `runtime-status ${status}`;
  runtime.innerHTML = `<span class="status-dot ${status}"></span><span>${label}</span>${detail ? `<small>${detail}</small>` : ""}`;
}

async function loadHomeState() {
  try {
    const [healthResponse, documentsResponse, offlineResponse, liveResponse] = await Promise.all([
      fetch("/health"), fetch("/documents"), fetch("/evaluation/offline"), fetch("/evaluation/live"),
    ]);
    if (![healthResponse, documentsResponse, offlineResponse, liveResponse].every((response) => response.ok)) {
      throw new Error("Local endpoint unavailable");
    }
    const [health, documents, offline, live] = await Promise.all([
      healthResponse.json(), documentsResponse.json(), offlineResponse.json(), liveResponse.json(),
    ]);
    document.querySelector("#homeProvider").textContent = health.provider;
    document.querySelector("#homeDocuments").textContent = documents.length;
    document.querySelector("#homeGates").textContent = `${offline.summary.gates_passed} / ${offline.summary.gates_total}`;
    document.querySelector("#homeRequests").textContent = live.total_requests;
    setRuntime("ok", "Local runtime", health.provider);
  } catch (error) {
    setRuntime("bad", "Runtime unavailable");
  }
}

loadHomeState();
