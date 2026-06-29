/* ==========================================================================
   Gold Circle Investments Ltd — QHSE Platform
   Main Application Script
   ========================================================================== */

/* --------------------------------------------------------------------------
   UTILITIES
   -------------------------------------------------------------------------- */

function escapeHtml(s) {
  if (s === null || s === undefined) return '';
  return String(s).replace(/[&<>"']/g, c =>
    ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;' })[c]
  );
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-GB');
}

function formatIdleTime(reportedAt) {
  if (!reportedAt) return 'Unknown';
  const diffMs = Date.now() - new Date(reportedAt).getTime();
  const minutes = Math.floor(diffMs / 60000);
  const hours   = Math.floor(minutes / 60);
  const days    = Math.floor(hours / 24);
  const parts   = [];
  if (days > 0)        parts.push(`${days}d`);
  if (hours % 24 > 0)  parts.push(`${hours % 24}h`);
  if (minutes % 60 > 0) parts.push(`${minutes % 60}m`);
  return parts.join(' ') || '0m';
}

/* --------------------------------------------------------------------------
   SIDEBAR — section show/hide
   The sidebar nav items each have data-section="<id>".
   Clicking one hides all sections and shows the target.
   -------------------------------------------------------------------------- */

function initSidebar() {
  const menuItems = document.querySelectorAll('.menu li[data-section]');
  if (!menuItems.length) return;

  const allSections = [
    'dashboard-section',
    'audit-section',
    'incident-section',
    'training-section',
    'docs-section'
  ];

  function showSection(sectionId) {
    allSections.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.classList.add('hidden');
    });
    const target = document.getElementById(sectionId);
    if (target) target.classList.remove('hidden');

    // Update active nav item
    menuItems.forEach(li => {
      li.classList.toggle('active', li.dataset.section === sectionId);
    });

    // Update breadcrumb if present
    const bc = document.getElementById('breadcrumb');
    if (bc) {
      const labels = {
        'dashboard-section':  'Home / Dashboard',
        'audit-section':      'Home / Audit Management / Audit Plan',
        'incident-section':   'Home / Incident Management',
        'training-section':   'Home / Training & Briefings',
        'docs-section':       'Home / Document Management',
      };
      bc.textContent = labels[sectionId] || 'Home';
    }
  }

  // Click handlers
  menuItems.forEach(item => {
    item.addEventListener('click', () => showSection(item.dataset.section));
  });

  // Show the section marked data-active on the sidebar div
  const sidebar = document.querySelector('.sidebar[data-active]');
  if (sidebar) {
    showSection(sidebar.dataset.active);
  }
}

/* --------------------------------------------------------------------------
   TABS — scoped to a parent container
   Each tab has data-tab="<content-id>".
   Only affects tabs/contents within the same nearest ancestor that contains both.
   -------------------------------------------------------------------------- */

function initTabs(root) {
  const container = root || document;
  const tabs = container.querySelectorAll(':scope .tab');
  if (!tabs.length) return;

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      // Find the closest ancestor that has both .tabs and .tab-content children
      const tabsBar = tab.closest('.tabs');
      if (!tabsBar) return;
      const section = tabsBar.closest('#audit-section, #incident-section, .main-content, body') || container;

      // Deactivate all tabs in this bar
      tabsBar.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      // Deactivate all tab-contents in this section
      section.querySelectorAll(':scope > .tab-content, .tab-content').forEach(c => {
        // Only deactivate contents that belong to this tab group
        if (tabsBar.querySelector(`[data-tab="${c.id}"]`)) {
          c.classList.remove('active');
        }
      });

      const targetId = tab.dataset.tab;
      const targetEl = section.querySelector('#' + targetId) || document.getElementById(targetId);
      if (targetEl) targetEl.classList.add('active');

      // Update page title/breadcrumb for audit section
      updateAuditPageInfo(targetId);

      // Render charts when incident dashboard tab opens
      if (targetId === 'incident-dashboard') renderDashboardCharts();
    });
  });
}

function updateAuditPageInfo(tabId) {
  const bc = document.getElementById('breadcrumb');
  const pt = document.getElementById('pageTitle');
  const map = {
    'audit-plan':       ['Home / Audit Management / Audit Plan',         'Audit Plan'],
    'new-audit':        ['Home / Audit Management / New Audit',          'New Audit'],
    'audit-details':    ['Audit Management / View All Audit / Details',  'Audit Details'],
    'incident-dashboard':['Home / Incident Management / Dashboard',      'Incident Management'],
    'all-incidents':    ['Home / Incident Management / All Incidents',   'All Incidents'],
    'new-incident':     ['Home / Incident Management / New Incident',    'New Incident'],
    'incident-details': ['Home / Incident Management / Details',         'Incident Details'],
    'capas':            ['Home / Incident Management / CAPA',            'CAPA'],
    'document-management':['Home / Incident Management / Documents',     'Document Management'],
    'trainings-briefings':['Home / Incident Management / Trainings',     'Trainings & Briefings'],
  };
  if (map[tabId]) {
    if (bc) bc.textContent = map[tabId][0];
    if (pt) pt.textContent = map[tabId][1];
  }
}

/* --------------------------------------------------------------------------
   AUDIT MANAGEMENT
   -------------------------------------------------------------------------- */

function setDefaultDates() {
  const today = new Date().toISOString().split('T')[0];
  ['audit-date', 'conducted-date', 'plan-date'].forEach(id => {
    const el = document.getElementById(id);
    if (el && !el.value) el.value = today;
  });
}

function saveAuditPlan() {
  const standard = document.getElementById('plan-standard');
  const date     = document.getElementById('plan-date');
  if (!standard?.value || !date?.value) {
    return alert('Please select both Standard and Plan Date.');
  }
  alert('Audit Plan saved successfully!');
}

function sendForApproval() {
  if (confirm('Send this audit plan for approval?')) {
    alert('Audit Plan sent for approval successfully!');
  }
}

function saveAudit() {
  const fields = ['organization','audit-type','audit-standard','scope',
                  'audit-date','audit-time','duration','auditor','lead-auditor','auditee'];
  let valid = true;
  fields.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    if (!el.value.trim()) {
      el.style.borderColor = 'var(--color-corporate-red)';
      valid = false;
    } else {
      el.style.borderColor = '';
    }
  });
  const shift = document.querySelector('input[name="shift"]:checked');
  if (!shift) {
    const opts = document.querySelector('.shift-options');
    if (opts) opts.style.outline = '2px solid var(--color-corporate-red)';
    valid = false;
  }
  if (!valid) return alert('Please fill in all required fields (*).');
  alert('Audit saved successfully!');
}

function updateAudit() {
  const fields = ['conducted-date','audit-summary','references'];
  let valid = true;
  fields.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    if (!el.value.trim()) {
      el.style.borderColor = 'var(--color-corporate-red)';
      valid = false;
    } else {
      el.style.borderColor = '';
    }
  });
  if (!valid) return alert('Please fill in all required fields.');
  alert('Audit details updated successfully!');
}

function initAuditPlanTable() {
  const months = ['January','February','March','April','May','June',
                  'July','August','September','October','November','December'];
  document.querySelectorAll('.planned-audit').forEach(icon => {
    icon.addEventListener('click', function () {
      const colIndex = this.parentElement.cellIndex - 2;
      const org = this.parentElement.parentElement.cells[1].textContent.trim();
      const monthName = months[colIndex] || 'Unknown';
      if (confirm(`Schedule audit for ${org} in ${monthName}?`)) {
        this.style.color = 'var(--color-orange)';
        setTimeout(() => { this.style.color = ''; }, 1200);
      }
    });
  });
}

/* --------------------------------------------------------------------------
   INCIDENT MANAGEMENT
   -------------------------------------------------------------------------- */

// In-memory store (demo). Seeded with examples.
let incidentData = {
  1: { id:1, title:'Near Miss — Admin Office',  department:'Administration', type:'Near Miss', date:'2025-10-08', severity:'Low',    status:'Open',        investigator:'HSE Officer', location:'Admin Block A', description:'Minor near miss in admin office.' },
  2: { id:2, title:'Equipment Failure — Pump 4', department:'Production',    type:'Incident',  date:'2025-10-05', severity:'High',   status:'In Progress', investigator:'Supervisor',  location:'Pump Station 4', description:'Pump failure in production area.' },
  3: { id:3, title:'QC Lab Issue',               department:'Quality Control',type:'Incident',  date:'2025-10-01', severity:'Medium', status:'Closed',      investigator:'Lead Auditor',location:'QC Lab',         description:'Quality control failure detected.' },
};
let nextIncidentId = 4;

function refreshIncidentTable() {
  const tbody = document.getElementById('incident-table-body');
  if (!tbody) return;
  tbody.innerHTML = '';
  Object.values(incidentData).sort((a, b) => a.id - b.id).forEach(it => {
    const statusClass = {
      'Open':           'status-open',
      'In Progress':    'status-in-progress',
      'Closed':         'status-closed',
    }[it.status] || 'status-open';

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${it.id}</td>
      <td>${escapeHtml(it.title)}</td>
      <td>${escapeHtml(it.department)}</td>
      <td>${formatDate(it.date)}</td>
      <td>${escapeHtml(it.severity || '—')}</td>
      <td><span class="status-badge ${statusClass}">${escapeHtml(it.status)}</span></td>
      <td style="display:flex;gap:6px;flex-wrap:wrap;">
        <button class="btn btn-primary btn-small" onclick="viewIncident(${it.id})">View</button>
        ${it.status !== 'Closed'
          ? `<button class="btn btn-success btn-small" onclick="closeIncident(${it.id})">Close</button>`
          : ''}
        <button class="btn btn-danger btn-small" onclick="deleteIncidentLocal(${it.id})">Delete</button>
      </td>`;
    tbody.appendChild(tr);
  });
  refreshDashboardKPIs();
}

function refreshDashboardKPIs() {
  const vals = Object.values(incidentData);
  const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
  set('kpi-open',       vals.filter(v => v.status === 'Open').length);
  set('kpi-inprogress', vals.filter(v => v.status === 'In Progress').length);
  set('kpi-closed',     vals.filter(v => v.status === 'Closed').length);
}

function filterIncidents() {
  const q = (document.getElementById('incidentSearch')?.value || '').toLowerCase();
  document.querySelectorAll('#incident-table-body tr').forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}

function viewIncident(id) {
  const data = incidentData[id];
  if (!data) return alert('Incident not found.');

  const set = (elId, val) => { const el = document.getElementById(elId); if (el) el.value = val || ''; };
  set('detail-id',          data.id);
  set('detail-title',       data.title);
  set('detail-department',  data.department);
  set('detail-type',        data.type);
  set('detail-date',        data.date);
  set('detail-severity',    data.severity);
  set('detail-description', data.description);
  set('detail-investigator',data.investigator);
  set('detail-location',    data.location);
  set('detail-rca',         data.rca || '');

  const statusEl = document.getElementById('detail-status');
  if (statusEl) statusEl.value = data.status;

  // Switch to Incident Details tab
  switchToTab('incident-details', '#incident-section');
}

function switchToTab(tabId, sectionSelector) {
  const section = document.querySelector(sectionSelector) || document;
  section.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  const target = section.querySelector('#' + tabId) || document.getElementById(tabId);
  if (target) target.classList.add('active');

  const tabsBar = section.querySelector('.tabs');
  if (tabsBar) {
    tabsBar.querySelectorAll('.tab').forEach(t => {
      t.classList.toggle('active', t.dataset.tab === tabId);
    });
  }
  updateAuditPageInfo(tabId);
}

function closeIncident(id) {
  if (!confirm('Mark this incident as Closed?')) return;
  if (incidentData[id]) incidentData[id].status = 'Closed';
  refreshIncidentTable();

  // Also persist to backend
  fetch(`/incidents/${id}/close`, { method: 'POST', credentials: 'same-origin' })
    .catch(() => {}); // silent — local state already updated
}

function deleteIncidentLocal(id) {
  if (!confirm('Delete this incident permanently?')) return;
  delete incidentData[id];
  refreshIncidentTable();

  fetch(`/incidents/${id}/delete`, { method: 'POST', credentials: 'same-origin' })
    .catch(() => {});
}

function updateIncidentDetails() {
  const id = parseInt(document.getElementById('detail-id')?.value);
  if (!id || !incidentData[id]) return alert('No incident selected.');
  incidentData[id].status      = document.getElementById('detail-status')?.value    || incidentData[id].status;
  incidentData[id].description = document.getElementById('detail-description')?.value || incidentData[id].description;
  incidentData[id].investigator= document.getElementById('detail-investigator')?.value || incidentData[id].investigator;
  incidentData[id].location    = document.getElementById('detail-location')?.value   || incidentData[id].location;
  incidentData[id].rca         = document.getElementById('detail-rca')?.value        || '';
  alert('Incident updated successfully.');
  refreshIncidentTable();
}

function submitIncident() {
  const get = id => document.getElementById(id)?.value?.trim() || '';

  const title      = get('incident-title');
  const department = get('incident-department');
  const type       = get('incident-type') || get('incident-category');
  const date       = get('incident-datetime') || get('incident-date');
  const severity   = get('incident-severity');
  const location   = get('incident-location');
  const description= get('incident-description');
  const investigator= get('incident-investigator');

  if (!title || !department || !type || !date) {
    return alert('Please fill in: Title, Department, Type, and Date.');
  }

  const employees        = parseFloat(get('incident-employees'))         || 0;
  const hoursPerEmployee = parseFloat(get('incident-hours-per-employee'))|| 0;
  const idleHours        = parseFloat(get('incident-idle-hours'))        || 0;
  const costPerHour      = parseFloat(get('incident-cost-per-hour'))     || 0;
  const hoursLost        = employees * hoursPerEmployee;
  const totalCost        = hoursLost * costPerHour;

  const id = nextIncidentId++;
  incidentData[id] = { id, title, department, type, date, severity, location,
    description, investigator, employees, hoursLost, costPerHour, totalCost, status: 'Open' };

  // Reset form
  const form = document.getElementById('newIncidentForm');
  if (form) form.reset();
  const fileList = document.getElementById('file-list');
  if (fileList) fileList.innerHTML = '';

  refreshIncidentTable();

  // Switch to All Incidents tab
  switchToTab('all-incidents', '#incident-section');

  // Persist to backend (non-blocking)
  fetch('/incidents/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify({ title, department, category: type, type, date, severity,
      location, description, investigator, employees_affected: employees,
      hours_per_employee: hoursPerEmployee, idle_hours: idleHours,
      cost_per_hour: costPerHour, hours_lost: hoursLost, total_cost: totalCost }),
  }).catch(() => {});
}

function calculateIncidentLoss() {
  const get = id => parseFloat(document.getElementById(id)?.value) || 0;
  const employees        = get('incident-employees');
  const hoursPerEmployee = get('incident-hours-per-employee');
  const costPerHour      = get('incident-cost-per-hour');
  const hoursLost        = employees * hoursPerEmployee;
  const totalCost        = hoursLost * costPerHour;

  const hlEl = document.getElementById('incident-hours-lost');
  const tcEl = document.getElementById('incident-total-cost');
  if (hlEl) hlEl.value = hoursLost + ' hours';
  if (tcEl) tcEl.value = '$' + totalCost.toFixed(2);
}

function captureGeo() {
  const out = document.getElementById('geo-result');
  if (!navigator.geolocation) {
    if (out) out.textContent = 'Geolocation not supported.';
    return;
  }
  if (out) out.textContent = 'Requesting location…';
  navigator.geolocation.getCurrentPosition(pos => {
    const coords = `${pos.coords.latitude.toFixed(6)}, ${pos.coords.longitude.toFixed(6)}`;
    const locEl = document.getElementById('incident-location');
    if (locEl) locEl.value = coords;
    if (out)   out.textContent = 'Captured: ' + coords;
  }, err => {
    if (out) out.textContent = 'Error: ' + err.message;
  }, { enableHighAccuracy: true, timeout: 10000 });
}

/* --------------------------------------------------------------------------
   CAPA
   -------------------------------------------------------------------------- */

function createCapa() {
  const incidentId = document.getElementById('capa-incident-id')?.value || '';
  const desc  = document.getElementById('capa-desc')?.value.trim();
  const owner = document.getElementById('capa-owner')?.value.trim();
  const due   = document.getElementById('capa-due')?.value;

  if (!desc || !owner || !due) {
    return alert('Please fill: Action Description, Owner, Due Date.');
  }

  const tableBody = document.querySelector('#capa-table tbody');
  if (!tableBody) return;
  const newId = tableBody.children.length + 1;
  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td>${newId}</td>
    <td>${incidentId ? escapeHtml(incidentId) : 'N/A'}</td>
    <td>${escapeHtml(desc)}</td>
    <td>${escapeHtml(owner)}</td>
    <td>${due}</td>
    <td><span class="status-badge status-open">Open</span></td>
    <td><button class="btn btn-success btn-small" onclick="markCapaComplete(this)">Mark Complete</button></td>`;
  tableBody.appendChild(tr);

  ['capa-incident-id','capa-desc','capa-owner','capa-due'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  updateCapaPieChart();
}

function markCapaComplete(btn) {
  const row = btn.closest('tr');
  const badge = row.querySelector('.status-badge');
  badge.textContent = 'Closed';
  badge.className = 'status-badge status-closed';
  btn.remove();
  updateCapaPieChart();
}

function renderCapas() {
  // Stub — CAPA data is managed client-side via createCapa()
  // This function exists to prevent ReferenceError on page load
}

/* --------------------------------------------------------------------------
   CHARTS
   -------------------------------------------------------------------------- */

let incidentBarChart = null;
let capaPieChart     = null;
let chartsRendered   = false;

function renderIncidentBarChart() {
  const ctx = document.getElementById('incident-bar-chart');
  if (!ctx || typeof Chart === 'undefined') return;
  if (incidentBarChart) incidentBarChart.destroy();
  incidentBarChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Jan','Feb','Mar','Apr','May','Jun'],
      datasets: [{ label: 'Incidents', data: [5,8,12,6,9,7], backgroundColor: '#F6B400', borderRadius: 6 }],
    },
    options: { responsive: true, plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } },
  });
}

function renderCapaPieChart() {
  const ctx = document.getElementById('capa-pie-overview');
  if (!ctx || typeof Chart === 'undefined') return;
  if (capaPieChart) capaPieChart.destroy();

  const rows = document.querySelectorAll('#capa-table tbody tr');
  let open = 0, inProgress = 0, closed = 0;
  if (!rows.length) { open = 5; inProgress = 3; closed = 7; }
  else rows.forEach(r => {
    const s = r.querySelector('.status-badge')?.textContent || '';
    if (s === 'Open') open++;
    else if (s === 'In Progress') inProgress++;
    else if (s === 'Closed') closed++;
  });

  capaPieChart = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ['Open','In Progress','Closed'],
      datasets: [{ data: [open, inProgress, closed],
        backgroundColor: ['#F57C00','#F6B400','#34D400'] }],
    },
    options: { responsive: true, plugins: { legend: { position: 'bottom' } } },
  });
}

function updateCapaPieChart() { renderCapaPieChart(); }

function renderDashboardCharts() {
  if (chartsRendered) return;
  chartsRendered = true;
  renderIncidentBarChart();
  renderCapaPieChart();
}

/* --------------------------------------------------------------------------
   DOCUMENT MANAGEMENT
   -------------------------------------------------------------------------- */

function uploadDocument() {
  const title = document.getElementById('doc-title')?.value.trim();
  const fileEl = document.getElementById('doc-file');
  if (!title || !fileEl?.value) return alert('Please fill all fields.');
  const tbody = document.getElementById('documentTable');
  if (!tbody) return;
  const row = tbody.insertRow();
  row.innerHTML = `<td>${tbody.rows.length}</td><td>${escapeHtml(title)}</td>
    <td>${escapeHtml(fileEl.value.split('\\').pop())}</td>
    <td>${new Date().toLocaleDateString()}</td>`;
  document.getElementById('documentUploadForm')?.reset();
}

/* --------------------------------------------------------------------------
   TRAININGS
   -------------------------------------------------------------------------- */

function addTraining() {
  const title  = document.getElementById('training-title')?.value.trim();
  const date   = document.getElementById('training-date')?.value;
  const fileEl = document.getElementById('training-file');
  if (!title || !date || !fileEl?.value) return alert('Please fill all fields.');
  const tbody = document.getElementById('trainingTable');
  if (!tbody) return;
  const row = tbody.insertRow();
  row.innerHTML = `<td>${tbody.rows.length}</td><td>${escapeHtml(title)}</td>
    <td>${date}</td><td>${escapeHtml(fileEl.value.split('\\').pop())}</td>`;
  document.getElementById('trainingForm')?.reset();
}

/* --------------------------------------------------------------------------
   FILE UPLOAD PREVIEW
   -------------------------------------------------------------------------- */

function initFilePreview() {
  const fileInput = document.getElementById('incident-files');
  if (!fileInput) return;
  fileInput.addEventListener('change', function () {
    const list = document.getElementById('file-list');
    if (!list) return;
    list.innerHTML = '';
    Array.from(this.files).forEach(f => {
      const div = document.createElement('div');
      div.className = 'note';
      div.textContent = `${f.name} (${Math.round(f.size / 1024)} KB)`;
      list.appendChild(div);
    });
  });
}

/* --------------------------------------------------------------------------
   SEARCH (table filter)
   -------------------------------------------------------------------------- */

function initSearch() {
  document.querySelectorAll('.search-input').forEach(input => {
    input.addEventListener('input', function () {
      const q = this.value.toLowerCase();
      const table = this.closest('.table-container, .form-container')?.querySelector('table');
      if (!table) return;
      table.querySelectorAll('tbody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  });
}

/* --------------------------------------------------------------------------
   EXPORT CSV
   -------------------------------------------------------------------------- */

function exportIncidents() {
  const vals = Object.values(incidentData);
  if (!vals.length) return alert('No incidents to export.');
  const header = ['ID','Title','Department','Date','Type','Severity','Status','Investigator','Location','Description'];
  const rows = vals.map(it => [it.id, it.title, it.department, it.date, it.type,
    it.severity, it.status, it.investigator||'', it.location||'', it.description||'']);
  const csv = [header, ...rows].map(r =>
    r.map(c => `"${String(c).replace(/"/g,'""')}"`).join(',')
  ).join('\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
  a.download = `incidents_${new Date().toISOString().slice(0,10)}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}

/* --------------------------------------------------------------------------
   BOOT — run everything once DOM is ready
   -------------------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
  // Sidebar section switching
  initSidebar();

  // Tabs (scoped to each section that has them)
  document.querySelectorAll('#audit-section, #incident-section').forEach(sec => initTabs(sec));

  // Set today's date in audit date fields
  setDefaultDates();

  // Audit plan table icon clicks
  initAuditPlanTable();

  // Incident table initial render
  refreshIncidentTable();

  // File upload preview
  initFilePreview();

  // Search inputs
  initSearch();

  // Render CAPA list (stub)
  renderCapas();

  // Wire audit buttons (guard against missing elements)
  document.getElementById('save-plan')     ?.addEventListener('click', saveAuditPlan);
  document.getElementById('send-approval') ?.addEventListener('click', sendForApproval);
  document.getElementById('save-audit')    ?.addEventListener('click', saveAudit);
  document.getElementById('update-audit')  ?.addEventListener('click', updateAudit);

  // Incident cost calculator
  ['incident-employees','incident-hours-per-employee','incident-cost-per-hour'].forEach(id => {
    document.getElementById(id)?.addEventListener('input', calculateIncidentLoss);
  });

  // Render charts if incident dashboard is the active tab on load
  if (document.getElementById('incident-dashboard')?.classList.contains('active')) {
    renderDashboardCharts();
  }
});
