(function () {
  const data = window.AUTHORSHIP_LEDGER_DATA;
  if (!data) {
    return;
  }

  const state = {
    search: "",
    depositState: "",
    band: "",
    sort: "score",
  };

  const metricGrid = document.getElementById("metric-grid");
  const gapGrid = document.getElementById("gap-grid");
  const tierTable = document.getElementById("tier-table");
  const projectGrid = document.getElementById("project-grid");
  const resultsCopy = document.getElementById("results-copy");
  const exportLinks = document.getElementById("export-links");

  function pct(value) {
    return `${Number(value).toFixed(1)}%`;
  }

  function renderMetrics() {
    const cards = [
      [data.metrics.trackedProjects, "Indexed projects", `${data.metrics.depositDrafts} deposit drafts generated`],
      [pct(data.metrics.highWorkflowReadyPercent), "High workflow readiness", `${data.metrics.highWorkflowReadyCount} projects`],
      [pct(data.metrics.institutionalDraftReadyPercent), "Institutional drafts ready", `${data.metrics.institutionalDraftReadyCount} projects`],
      [pct(data.metrics.fullyRegistrablePercent), "Fully registrable", `${data.metrics.fullyRegistrableCount} projects`],
    ];
    metricGrid.innerHTML = cards.map(([value, label, note]) => `
      <article class="metric-card">
        <span class="metric-value">${value}</span>
        <span>${label}</span>
        <span class="metric-note">${note}</span>
      </article>
    `).join("");
  }

  function renderExports() {
    const links = [
      ["Deposit Manifest", data.project.links.depositManifest, "Aggregated DOI deposit queue"],
      ["ORCID Requests", data.project.links.orcidRequests, "Contributor identifier intake templates"],
      ["CRediT Templates", data.project.links.creditTemplates, "Contributor role scaffolds"],
      ["License Recommendations", data.project.links.licenseRecommendations, "SPDX-style recommendations"],
      ["E156 Submission", data.project.links.e156, "Paper, protocol, metadata, and reader"],
      ["GitHub Repo", data.project.links.repo, "Full code and bundled snapshots"],
    ];
    exportLinks.innerHTML = links.map(([title, href, text]) => `
      <a class="export-link" href="${href}">
        <strong>${title}</strong>
        <span>${text}</span>
      </a>
    `).join("");
  }

  function renderGaps() {
    gapGrid.innerHTML = data.gapBreakdown.map((item) => `
      <article class="chip">
        <strong>${item.label}</strong>
        <p>${item.count} projects</p>
      </article>
    `).join("");
  }

  function renderTiers() {
    tierTable.innerHTML = data.tiers.map((item) => `
      <tr>
        <td>${item.tier}</td>
        <td>${item.count}</td>
        <td>${item.meanScore.toFixed(1)}</td>
        <td>${item.institutionalDrafts}</td>
      </tr>
    `).join("");
  }

  function filteredProjects() {
    const q = state.search.trim().toLowerCase();
    const projects = data.projects.filter((project) => {
      if (state.depositState && project.depositState !== state.depositState) {
        return false;
      }
      if (state.band && project.workflowBand !== state.band) {
        return false;
      }
      if (!q) {
        return true;
      }
      return [
        project.name,
        project.tier,
        project.recordType,
        project.targetJournal,
        project.primaryGap,
        project.depositState,
      ].join(" ").toLowerCase().includes(q);
    });

    const sorters = {
      score: (a, b) => b.workflowReadinessScore - a.workflowReadinessScore || a.name.localeCompare(b.name),
      name: (a, b) => a.name.localeCompare(b.name),
    };
    return projects.sort(sorters[state.sort]);
  }

  function renderProjects() {
    const projects = filteredProjects();
    resultsCopy.textContent = `${projects.length} queue pages shown`;
    projectGrid.innerHTML = projects.map((project) => `
      <a class="project-card" href="queues/${project.slug}.html">
        <div class="pill-row">
          <span class="pill ${project.workflowBand}">${project.workflowBand} workflow</span>
          <span class="pill">${project.depositState}</span>
          <span class="pill">${project.tier}</span>
        </div>
        <div>
          <h3>${project.name}</h3>
          <p class="hero-text">${project.queueSummary}</p>
        </div>
        <div class="score">${project.workflowReadinessScore}</div>
        <div class="project-meta">
          <span>License: ${project.recommendedLicense}</span>
          <span>Journal: ${project.targetJournal || "Not preserved"}</span>
          <span>Primary gap: ${project.primaryGap}</span>
        </div>
      </a>
    `).join("");
  }

  function bindEvents() {
    document.getElementById("search-input").addEventListener("input", (event) => {
      state.search = event.target.value;
      renderProjects();
    });
    document.getElementById("state-select").addEventListener("change", (event) => {
      state.depositState = event.target.value;
      renderProjects();
    });
    document.getElementById("band-select").addEventListener("change", (event) => {
      state.band = event.target.value;
      renderProjects();
    });
    document.getElementById("sort-select").addEventListener("change", (event) => {
      state.sort = event.target.value;
      renderProjects();
    });
  }

  renderMetrics();
  renderExports();
  renderGaps();
  renderTiers();
  bindEvents();
  renderProjects();
}());
