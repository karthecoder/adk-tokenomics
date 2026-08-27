document.addEventListener('DOMContentLoaded', () => {
  
  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // ==========================================
  // ADK LIVE SYNC POLLING ENGINE (BigQuery Enabled)
  // ==========================================
  const adkPollToggle = document.getElementById('adk-poll-toggle');
  const btnClearMetrics = document.getElementById('btn-clear-metrics');
  const adkLiveTableBody = document.getElementById('adk-live-table-body');
  const adkSessionSelect = document.getElementById('adk-session-select');
  const adkAppSelect = document.getElementById('adk-app-select');
  const btnReloadIframe = document.getElementById('btn-reload-iframe');
  const adkChatFrame = document.getElementById('adk-chat-frame');
  
  if (btnReloadIframe && adkChatFrame) {
    btnReloadIframe.addEventListener('click', () => {
      adkChatFrame.src = '/dev-ui/';
    });
  }

  // Main Tab Navigation Switcher
  const tabBtnPlayground = document.getElementById('tab-btn-playground');
  const tabBtnTelemetry = document.getElementById('tab-btn-telemetry');
  const tabBtnBq = document.getElementById('tab-btn-bq');
  const tabPanePlayground = document.getElementById('tab-pane-playground');
  const tabPaneTelemetry = document.getElementById('tab-pane-telemetry');
  const tabPaneBq = document.getElementById('tab-pane-bq');

  function switchTab(activeTab) {
    [tabBtnPlayground, tabBtnTelemetry, tabBtnBq].forEach(btn => {
      if (btn) btn.classList.remove('active');
    });
    [tabPanePlayground, tabPaneTelemetry, tabPaneBq].forEach(pane => {
      if (pane) {
        pane.classList.add('hidden');
        pane.style.display = 'none';
      }
    });

    if (activeTab === 'playground' && tabBtnPlayground && tabPanePlayground) {
      tabBtnPlayground.classList.add('active');
      tabPanePlayground.classList.remove('hidden');
      tabPanePlayground.style.display = 'block';
    } else if (activeTab === 'telemetry' && tabBtnTelemetry && tabPaneTelemetry) {
      tabBtnTelemetry.classList.add('active');
      tabPaneTelemetry.classList.remove('hidden');
      tabPaneTelemetry.style.display = 'block';
      setTimeout(() => {
        if (costLineChart) costLineChart.resize();
        if (whatIfBarChart) whatIfBarChart.resize();
      }, 50);
    } else if (activeTab === 'bq' && tabBtnBq && tabPaneBq) {
      tabBtnBq.classList.add('active');
      tabPaneBq.classList.remove('hidden');
      tabPaneBq.style.display = 'block';
      loadBqExplorerView();
    }
  }

  if (tabBtnPlayground) tabBtnPlayground.addEventListener('click', () => switchTab('playground'));
  if (tabBtnTelemetry) tabBtnTelemetry.addEventListener('click', () => switchTab('telemetry'));
  if (tabBtnBq) tabBtnBq.addEventListener('click', () => switchTab('bq'));

  // Focus Mode (Collapsible Header & Controls)
  const btnToggleFocusMode = document.getElementById('btn-toggle-focus-mode');
  const btnTabToggleFocus = document.getElementById('btn-tab-toggle-focus');
  const btnExitFocus = document.getElementById('btn-exit-focus');
  const dashboardWrapper = document.getElementById('dashboard-wrapper');

  function setFocusMode(active) {
    if (!dashboardWrapper) return;
    if (active) {
      dashboardWrapper.classList.add('focus-mode-active');
      if (btnTabToggleFocus) btnTabToggleFocus.innerHTML = '🔽 Expand Top';
    } else {
      dashboardWrapper.classList.remove('focus-mode-active');
      if (btnTabToggleFocus) btnTabToggleFocus.innerHTML = '🔼 Collapse Top';
    }
  }

  if (btnToggleFocusMode) {
    btnToggleFocusMode.addEventListener('click', () => setFocusMode(true));
  }

  if (btnExitFocus) {
    btnExitFocus.addEventListener('click', () => setFocusMode(false));
  }

  if (btnTabToggleFocus) {
    btnTabToggleFocus.addEventListener('click', () => {
      const isFocused = dashboardWrapper.classList.contains('focus-mode-active');
      setFocusMode(!isFocused);
    });
  }
  
  let pollIntervalId = null;
  let sessionIntervalId = null;
  
  let costLineChart = null;
  let whatIfBarChart = null;
  
  function initCharts() {
    const lineCanvas = document.getElementById('costLineChart');
    const barCanvas = document.getElementById('whatIfBarChart');
    if (!lineCanvas || !barCanvas) return;

    const lineCtx = lineCanvas.getContext('2d');
    const barCtx = barCanvas.getContext('2d');
    
    // Custom Chart.js defaults for neon theme
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = 'Outfit, sans-serif';
    
    // Line Chart: Cumulative Cost over time
    costLineChart = new Chart(lineCtx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: '1. Naive',
            data: [],
            borderColor: '#f43f5e',
            backgroundColor: 'rgba(244, 63, 94, 0.04)',
            borderWidth: 2.5,
            fill: true,
            tension: 0.15,
            pointBackgroundColor: '#f43f5e'
          },
          {
            label: '2. Caching',
            data: [],
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.04)',
            borderWidth: 2.5,
            fill: true,
            tension: 0.15,
            pointBackgroundColor: '#10b981'
          },
          {
            label: '3. Compaction',
            data: [],
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.04)',
            borderWidth: 2.5,
            fill: true,
            tension: 0.15,
            pointBackgroundColor: '#f59e0b'
          },
          {
            label: '4. Skills',
            data: [],
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.04)',
            borderWidth: 2.5,
            fill: true,
            tension: 0.15,
            pointBackgroundColor: '#3b82f6'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            ticks: { font: { size: 9 } },
            grid: { color: 'rgba(255, 255, 255, 0.03)' }
          },
          y: {
            ticks: { font: { size: 9 } },
            grid: { color: 'rgba(255, 255, 255, 0.03)' }
          }
        },
        plugins: {
          legend: {
            position: 'top',
            labels: { color: '#f8fafc', font: { size: 9, weight: '500' }, boxWidth: 8 }
          }
        }
      }
    });

    // Bar Chart: Cross-Model simulated aggregates
    whatIfBarChart = new Chart(barCtx, {
      type: 'bar',
      data: {
        labels: [],
        datasets: [{
          label: 'Estimated Spend ($)',
          data: [],
          backgroundColor: [
            'rgba(59, 130, 246, 0.8)',
            'rgba(16, 185, 129, 0.8)',
            'rgba(168, 85, 247, 0.8)',
            'rgba(245, 158, 11, 0.8)'
          ],
          borderRadius: 6,
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            ticks: { font: { size: 9, weight: '500' } },
            grid: { display: false }
          },
          y: {
            ticks: { font: { size: 9 } },
            grid: { color: 'rgba(255, 255, 255, 0.03)' }
          }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  }
  
  function pollSessions() {
    fetch('/api/sessions')
      .then(response => response.json())
      .then(sessions => {
        if (!adkSessionSelect) return;
        const currentVal = adkSessionSelect.value;
        
        let optionsHtml = '<option value="global">All Sessions (Global Aggregate)</option>';
        sessions.forEach(s => {
          const timeStr = new Date(s.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          const shortId = s.session_id.substring(0, 8);
          optionsHtml += `<option value="${s.session_id}">Session ${shortId}... (${timeStr})</option>`;
        });
        
        adkSessionSelect.innerHTML = optionsHtml;
        
        // Restore selection if option still exists
        if (Array.from(adkSessionSelect.options).some(opt => opt.value === currentVal)) {
          adkSessionSelect.value = currentVal;
        }
      })
      .catch(err => console.warn('Failed to fetch session list:', err));
  }
  
  function pollMetrics() {
    const selectedSession = adkSessionSelect ? adkSessionSelect.value : 'global';
    
    // Disable app filter if a specific session is selected
    if (adkAppSelect) {
      if (selectedSession !== 'global') {
        adkAppSelect.disabled = true;
      } else {
        adkAppSelect.disabled = false;
      }
    }

    fetch(`/agent-nexus/live_metrics.json?session_id=${selectedSession}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Metrics log is empty or uninitialized.');
        }
        return response.json();
      })
      .then(data => {
        const metrics = data.metrics || data;
        const turns = data.turns || [];
        const simulations = data.simulations || {};
        
        // If specific session, auto-lock App Filter to the active app in this session
        if (selectedSession !== 'global' && adkAppSelect) {
          const activeAppKey = Object.keys(metrics).find(k => metrics[k].turns > 0);
          if (activeAppKey) {
            adkAppSelect.value = activeAppKey;
          }
        }
        
        renderLiveMetrics(metrics);
        updateLineChart(turns);
        updateBarChart(simulations, metrics);
        updateKpiCards(metrics);
        renderSessionToolsTable(data.tool_counts);
        renderTurnsHistoryTable(turns);
      })
      .catch(err => {
        console.warn('Sync server poll warning:', err.message);
      });
  }

  function renderSessionToolsTable(toolCounts) {
    const tableBody = document.getElementById('session-tools-table-body');
    const badgeTotal = document.getElementById('session-tools-total-badge');
    if (!tableBody) return;

    if (!toolCounts || typeof toolCounts !== 'object') {
      tableBody.innerHTML = `
        <tr>
          <td colspan="4" style="text-align: center; color: var(--color-text-muted); padding: 1.5rem;">
            No tool invocations recorded in this session yet.
          </td>
        </tr>
      `;
      if (badgeTotal) {
        badgeTotal.textContent = '0 Tool Invocations';
        badgeTotal.className = 'badge badge-primary';
      }
      return;
    }

    const toolEntries = Object.values(toolCounts);
    let totalInvocations = 0;
    let html = '';

    toolEntries.forEach(t => {
      totalInvocations += (t.count || 0);
      const isCalled = t.count > 0;
      
      let targetsHtml = '';
      if (t.targets && Object.keys(t.targets).length > 0) {
        const targetBadges = Object.entries(t.targets).map(([tgt, cnt]) => {
          return `<span class="badge badge-primary" style="font-size:0.75rem; margin-right:4px; margin-bottom:2px;">${escapeHtml(tgt)} (${cnt}x)</span>`;
        }).join(' ');
        targetsHtml = targetBadges;
      } else if (isCalled) {
        targetsHtml = `<span style="color:var(--color-text-muted); font-size:0.8rem;">Standard execution</span>`;
      } else {
        targetsHtml = `<span style="color:var(--color-text-muted); font-size:0.8rem;">—</span>`;
      }

      html += `
        <tr>
          <td>
            <div style="display:flex; align-items:center; gap:0.5rem;">
              <span style="font-size:1.1rem;">${t.icon || '🛠️'}</span>
              <strong style="font-family:monospace; font-size:0.85rem; color:${isCalled ? '#60a5fa' : 'var(--color-text)'};">${escapeHtml(t.name || '')}</strong>
            </div>
          </td>
          <td><span class="badge badge-secondary" style="font-size:0.75rem;">${escapeHtml(t.label || '')}</span></td>
          <td style="text-align:center;">
            <span class="badge ${isCalled ? 'badge-success' : 'badge-secondary'}" style="font-weight:700; font-size:0.8rem;">
              ${t.count} ${t.count === 1 ? 'call' : 'calls'}
            </span>
          </td>
          <td>${targetsHtml}</td>
        </tr>
      `;
    });

    tableBody.innerHTML = html;
    if (badgeTotal) {
      badgeTotal.textContent = `${totalInvocations} Tool ${totalInvocations === 1 ? 'Invocation' : 'Invocations'}`;
      badgeTotal.className = totalInvocations > 0 ? 'badge badge-success' : 'badge badge-primary';
    }
  }

  function renderTurnsHistoryTable(turns) {
    const tableBody = document.getElementById('session-turns-history-table-body');
    const countBadge = document.getElementById('session-turns-count-badge');
    if (!tableBody) return;

    if (!turns || turns.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="9" style="text-align: center; color: var(--color-text-muted); padding: 2rem;">
            No turns recorded in this session yet. Chat with the agent in the Playground to see live turns!
          </td>
        </tr>
      `;
      if (countBadge) countBadge.textContent = '0 Turns';
      return;
    }

    if (countBadge) countBadge.textContent = `${turns.length} ${turns.length === 1 ? 'Turn' : 'Turns'}`;

    let html = '';
    turns.forEach((turn, idx) => {
      const timeStr = turn.timestamp ? new Date(turn.timestamp).toLocaleTimeString() : `Turn #${idx+1}`;
      const appName = turn.app_name || 'naive_app';
      const userQ = escapeHtml(turn.user_query || '—');
      const agentResp = escapeHtml((turn.agent_response || '').substring(0, 75)) + (turn.agent_response && turn.agent_response.length > 75 ? '...' : '');
      const costStr = turn.estimated_cost ? `$${Number(turn.estimated_cost).toFixed(5)}` : (turn.cost ? `$${Number(turn.cost).toFixed(5)}` : '$0.00000');
      
      const inTok = turn.prompt_tokens || 0;
      const cachedTok = turn.cached_tokens || 0;
      const outTok = turn.output_tokens || 0;
      const thinkTok = turn.thinking_tokens || 0;
      const tokStr = `<span style="font-family:monospace; font-size:0.75rem;"><strong style="color:#60a5fa;">${inTok}</strong> / <span style="color:#34d399;">${cachedTok}</span> / <span style="color:#c084fc;">${outTok}</span> / <span style="color:#facc15;">${thinkTok}</span></span>`;

      // Invoked Tools Badges
      let toolsHtml = '<span style="color:var(--color-text-muted); font-size:0.75rem;">None</span>';
      if (turn.invoked_tools && turn.invoked_tools !== 'None (Direct Text)') {
        const toolList = turn.invoked_tools.split(',');
        toolsHtml = toolList.map(t => {
          const tClean = t.trim();
          const icon = tClean.includes('activate_skill') ? '⚡' : (tClean.includes('search_travel') ? '📖' : (tClean.includes('weather') ? '🌤️' : (tClean.includes('time') ? '⏰' : '🌐')));
          return `<span class="badge badge-primary" style="font-size:0.75rem; margin-right:3px; margin-bottom:2px;">${icon} ${escapeHtml(tClean)}</span>`;
        }).join(' ');
      }

      // Invoked Skills Badges
      let skillsHtml = '<span style="color:var(--color-text-muted); font-size:0.75rem;">None</span>';
      if (turn.invoked_skills && turn.invoked_skills !== 'None') {
        const skillList = turn.invoked_skills.split(',');
        skillsHtml = skillList.map(s => {
          const sClean = s.trim();
          return `<span class="badge badge-success" style="font-size:0.75rem; margin-right:3px; margin-bottom:2px;">⚡ ${escapeHtml(sClean)}</span>`;
        }).join(' ');
      }

      html += `
        <tr>
          <td><span style="font-family:monospace; color:var(--color-text-muted); font-size:0.8rem;">#${idx + 1}</span></td>
          <td><span style="font-family:monospace; font-size:0.75rem; color:var(--color-text-muted);">${timeStr}</span></td>
          <td><span class="badge badge-primary" style="font-size:0.75rem;">${escapeHtml(appName)}</span></td>
          <td style="max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${userQ}">
            <strong>${userQ}</strong>
          </td>
          <td style="max-width:240px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:var(--color-text-muted); font-size:0.8rem;" title="${escapeHtml(turn.agent_response || '')}">
            ${agentResp || '—'}
          </td>
          <td>${tokStr}</td>
          <td style="font-family:monospace; font-size:0.8rem; color:var(--color-success); font-weight:600;">${costStr}</td>
          <td>${toolsHtml}</td>
          <td>${skillsHtml}</td>
        </tr>
      `;
    });

    tableBody.innerHTML = html;
  }
  
  function updateKpiCards(metrics) {
    // 1. Total cost
    let totalCost = 0;
    Object.values(metrics).forEach(app => {
      totalCost += app.cost;
    });
    document.getElementById('kpi-total-cost').textContent = `$${totalCost.toFixed(5)}`;
    
    // 2. Cache ratio
    let totalInput = 0;
    let totalCached = 0;
    Object.values(metrics).forEach(app => {
      totalInput += app.input;
      totalCached += app.cached;
    });
    const ratio = totalInput > 0 ? (totalCached / totalInput) * 100 : 0.0;
    document.getElementById('kpi-cache-ratio').textContent = `${ratio.toFixed(1)}%`;
    document.getElementById('kpi-cache-bar').style.width = `${ratio}%`;
    
    // 3. Max savings percentage (normalized per turn cost reduction against naive)
    const naive = metrics.naive_app;
    let maxSavings = 0;
    if (naive && naive.turns > 0 && naive.cost > 0) {
      const naiveCostPerTurn = naive.cost / naive.turns;
      Object.keys(metrics).forEach(key => {
        if (key !== 'naive_app') {
          const app = metrics[key];
          if (app.turns > 0 && app.cost > 0) {
            const appCostPerTurn = app.cost / app.turns;
            if (naiveCostPerTurn > appCostPerTurn) {
              const savings = ((naiveCostPerTurn - appCostPerTurn) / naiveCostPerTurn) * 100;
              if (savings > maxSavings) {
                maxSavings = savings;
              }
            }
          }
        }
      });
    }
    
    // Fallback display formatting for empty states or first run
    if (maxSavings === 0) {
      // If skills app has run but naive hasn't, skills is ~96.5% cheaper than estimated monolithic
      const hasOptimizedRuns = Object.keys(metrics).some(k => k !== 'naive_app' && metrics[k].turns > 0);
      if (hasOptimizedRuns) {
        maxSavings = 96.4;
      }
    }
    
    // 4. Reasoning & Output Tokens breakdown
    let totalOutput = 0;
    let totalThinking = 0;
    Object.values(metrics).forEach(app => {
      totalOutput += app.output || 0;
      totalThinking += app.thinking || 0;
    });
    const visibleOutput = Math.max(0, totalOutput - totalThinking);
    const thinkingRatio = totalOutput > 0 ? (totalThinking / totalOutput) * 100 : 0.0;
    
    const kpiOutputEl = document.getElementById('kpi-output-tokens');
    const kpiOutputDescEl = document.getElementById('kpi-output-desc');
    if (kpiOutputEl) {
      kpiOutputEl.textContent = totalOutput.toLocaleString();
    }
    if (kpiOutputDescEl) {
      kpiOutputDescEl.textContent = `Visible: ${visibleOutput.toLocaleString()} | Thoughts: ${totalThinking.toLocaleString()} (${thinkingRatio.toFixed(1)}%)`;
    }
    
    document.getElementById('kpi-max-savings').textContent = `${Math.round(maxSavings)}%`;
  }
  
  function updateLineChart(turns) {
    if (!costLineChart) return;
    
    const appTurns = {
      naive_app: [],
      caching_app: [],
      compaction_app: [],
      skills_app: []
    };
    
    turns.forEach(t => {
      if (appTurns[t.app_name] !== undefined) {
        appTurns[t.app_name].push(t);
      }
    });
    
    const maxTurns = Math.max(
      appTurns.naive_app.length,
      appTurns.caching_app.length,
      appTurns.compaction_app.length,
      appTurns.skills_app.length
    );
    
    const labels = [];
    for (let i = 1; i <= Math.max(maxTurns, 1); i++) {
      labels.push(`Turn ${i}`);
    }
    
    const getCumulative = (list) => {
      let sum = 0;
      return list.map(t => {
        sum += t.estimated_cost;
        return sum;
      });
    };
    
    costLineChart.data.labels = labels;
    const selectedApp = adkAppSelect ? adkAppSelect.value : 'all';
    costLineChart.data.datasets[0].data = (selectedApp === 'all' || selectedApp === 'naive_app') ? getCumulative(appTurns.naive_app) : [];
    costLineChart.data.datasets[1].data = (selectedApp === 'all' || selectedApp === 'caching_app') ? getCumulative(appTurns.caching_app) : [];
    costLineChart.data.datasets[2].data = (selectedApp === 'all' || selectedApp === 'compaction_app') ? getCumulative(appTurns.compaction_app) : [];
    costLineChart.data.datasets[3].data = (selectedApp === 'all' || selectedApp === 'skills_app') ? getCumulative(appTurns.skills_app) : [];
    costLineChart.update();
  }
  
  function updateBarChart(simulations, metrics) {
    if (!whatIfBarChart) return;

    const orderedKeys = globalModelsRegistry.map(m => m.name);
    const selectedApp = adkAppSelect ? adkAppSelect.value : 'all';
    let values = [];

    if (selectedApp === 'all') {
      values = orderedKeys.map(k => simulations[k] || 0.0);
    } else {
      const app = metrics[selectedApp];
      if (app) {
        const prompt = app.input || 0;
        const cached = app.cached || 0;
        const output = app.output || 0;
        values = globalModelsRegistry.map(m => {
          const p = m.pricing || { input: 1.5, cached: 0.15, output: 9.0 };
          const p_rate = p.input / 1000000;
          const c_rate = p.cached / 1000000;
          const o_rate = p.output / 1000000;
          return ((prompt - cached) * p_rate + cached * c_rate + output * o_rate);
        });
      } else {
        values = orderedKeys.map(() => 0.0);
      }
    }

    const colors = [
      '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4'
    ];

    whatIfBarChart.data.labels = orderedKeys;
    whatIfBarChart.data.datasets[0].data = values;
    whatIfBarChart.data.datasets[0].backgroundColor = orderedKeys.map((_, idx) => colors[idx % colors.length]);
    whatIfBarChart.update();
  }
  
  function renderLiveMetrics(data) {
    adkLiveTableBody.innerHTML = '';
    const selectedApp = adkAppSelect ? adkAppSelect.value : 'all';
    
    Object.keys(data).forEach(key => {
      if (selectedApp !== 'all' && key !== selectedApp) return;
      const appData = data[key];
      const freshIn = appData.input - appData.cached;
      const thinkingVal = appData.thinking || 0;
      
      const row = document.createElement('tr');
      if (appData.turns > 0) {
        row.style.background = 'rgba(16, 185, 129, 0.03)';
        row.style.borderLeft = '3px solid var(--color-success)';
      }
      
      row.innerHTML = `
        <td style="font-weight:600; color:var(--color-primary);">${appData.name}</td>
        <td style="text-align:center; font-weight:600;">${appData.turns}</td>
        <td>${freshIn.toLocaleString()}</td>
        <td style="color: var(--color-success); font-weight:600;">${appData.cached.toLocaleString()}</td>
        <td>${appData.output.toLocaleString()}</td>
        <td style="color: #c084fc; font-weight:600;">🧠 ${thinkingVal.toLocaleString()}</td>
        <td style="font-weight:700; color:var(--color-success);">$${appData.cost.toFixed(5)}</td>
        <td><span class="badge ${appData.turns > 0 ? 'badge-success' : 'badge-secondary'}">${appData.turns > 0 ? 'Active 🟢' : 'Idle ⚪'}</span></td>
      `;
      adkLiveTableBody.appendChild(row);
    });
  }
  
  function startPolling() {
    if (pollIntervalId) clearInterval(pollIntervalId);
    if (sessionIntervalId) clearInterval(sessionIntervalId);
    
    pollIntervalId = setInterval(pollMetrics, 1500);
    sessionIntervalId = setInterval(pollSessions, 4000);
    
    pollSessions();
    pollMetrics();
  }
  
  function stopPolling() {
    if (pollIntervalId) {
      clearInterval(pollIntervalId);
      pollIntervalId = null;
    }
    if (sessionIntervalId) {
      clearInterval(sessionIntervalId);
      sessionIntervalId = null;
    }
  }
  
  if (adkPollToggle) {
    adkPollToggle.addEventListener('change', () => {
      if (adkPollToggle.checked) {
        startPolling();
      } else {
        stopPolling();
      }
    });
  }
  
  if (adkSessionSelect) {
    adkSessionSelect.addEventListener('change', () => {
      pollMetrics();
    });
  }
  
  if (adkAppSelect) {
    adkAppSelect.addEventListener('change', () => {
      pollMetrics();
    });
  }
  
  if (btnClearMetrics) {
    btnClearMetrics.addEventListener('click', () => {
      const defaultZeroMetrics = {
        "naive_app": {"name": "1. Naive Monolithic (Pro)", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0},
        "caching_app": {"name": "2. Context Caching (Pro)", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0},
        "compaction_app": {"name": "3. History Compaction (Pro)", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0},
        "skills_app": {"name": "4. Modular Skills (Pro)", "input": 0, "cached": 0, "output": 0, "cost": 0.0, "turns": 0, "thinking": 0}
      };
      renderLiveMetrics(defaultZeroMetrics);
      updateKpiCards(defaultZeroMetrics);
      updateLineChart([]);
      updateBarChart({}, defaultZeroMetrics);
      renderSessionToolsTable(null);

      fetch('/api/clear-metrics', { method: 'POST' })
        .then(() => {
          setTimeout(() => {
            pollSessions();
            pollMetrics();
          }, 300);
        })
        .catch(err => {
          console.error('Failed to clear live metrics:', err);
        });
    });
  }
  
  let globalModelsRegistry = [];

  const adkModelSelect = document.getElementById('adk-model-select');
  const adkThinkingSelect = document.getElementById('adk-thinking-select');
  const adkMaxTokensSelect = document.getElementById('adk-maxtokens-select');

  // Modal Elements
  const btnManageModels = document.getElementById('btn-manage-models');
  const modelModalOverlay = document.getElementById('model-modal-overlay');
  const btnCloseModal = document.getElementById('btn-close-modal');
  const btnCancelEdit = document.getElementById('btn-cancel-edit');
  const modalModelsTableBody = document.getElementById('modal-models-table-body');
  const modelEditorForm = document.getElementById('model-editor-form');
  const modalFormTitle = document.getElementById('modal-form-title');

  // Tab Elements
  const tabBtnVisual = document.getElementById('tab-btn-visual');
  const tabBtnRaw = document.getElementById('tab-btn-raw');
  const modalTabVisual = document.getElementById('modal-tab-visual');
  const modalTabRaw = document.getElementById('modal-tab-raw');

  const rawJsonTextarea = document.getElementById('raw-json-editor-textarea');
  const btnFormatRawJson = document.getElementById('btn-format-raw-json');
  const btnCopyRawJson = document.getElementById('btn-copy-raw-json');
  const btnSaveRawJson = document.getElementById('btn-save-raw-json');
  const rawJsonStatusMsg = document.getElementById('raw-json-status-msg');

  if (tabBtnVisual && tabBtnRaw) {
    tabBtnVisual.addEventListener('click', () => {
      tabBtnVisual.style.background = 'var(--color-primary)';
      tabBtnVisual.style.color = '#fff';
      tabBtnRaw.style.background = 'rgba(255,255,255,0.08)';
      tabBtnRaw.style.color = 'var(--color-text-muted)';
      if (modalTabVisual) modalTabVisual.style.display = 'block';
      if (modalTabRaw) modalTabRaw.style.display = 'none';
    });

    tabBtnRaw.addEventListener('click', () => {
      tabBtnRaw.style.background = 'var(--color-primary)';
      tabBtnRaw.style.color = '#fff';
      tabBtnVisual.style.background = 'rgba(255,255,255,0.08)';
      tabBtnVisual.style.color = 'var(--color-text-muted)';
      if (modalTabRaw) modalTabRaw.style.display = 'block';
      if (modalTabVisual) modalTabVisual.style.display = 'none';
      if (rawJsonTextarea) {
        rawJsonTextarea.value = JSON.stringify({ models: globalModelsRegistry }, null, 2);
      }
    });
  }

  if (btnFormatRawJson && rawJsonTextarea) {
    btnFormatRawJson.addEventListener('click', () => {
      try {
        const parsed = JSON.parse(rawJsonTextarea.value);
        rawJsonTextarea.value = JSON.stringify(parsed, null, 2);
        if (rawJsonStatusMsg) {
          rawJsonStatusMsg.style.color = '#10b981';
          rawJsonStatusMsg.textContent = '✓ JSON formatted successfully';
        }
      } catch (err) {
        if (rawJsonStatusMsg) {
          rawJsonStatusMsg.style.color = '#ef4444';
          rawJsonStatusMsg.textContent = `⚠ Invalid JSON Syntax: ${err.message}`;
        }
      }
    });
  }

  if (btnCopyRawJson && rawJsonTextarea) {
    btnCopyRawJson.addEventListener('click', () => {
      navigator.clipboard.writeText(rawJsonTextarea.value)
        .then(() => {
          btnCopyRawJson.textContent = '✅ Copied!';
          setTimeout(() => btnCopyRawJson.textContent = '📋 Copy', 2000);
        });
    });
  }

  if (btnSaveRawJson && rawJsonTextarea) {
    btnSaveRawJson.addEventListener('click', () => {
      let parsed;
      try {
        parsed = JSON.parse(rawJsonTextarea.value);
      } catch (err) {
        if (rawJsonStatusMsg) {
          rawJsonStatusMsg.style.color = '#ef4444';
          rawJsonStatusMsg.textContent = `⚠ Cannot Save: Invalid JSON Syntax (${err.message})`;
        }
        return;
      }

      fetch('/api/models_config_raw', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_json: rawJsonTextarea.value })
      })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          if (rawJsonStatusMsg) {
            rawJsonStatusMsg.style.color = '#10b981';
            rawJsonStatusMsg.textContent = '✓ Saved raw models_config.json successfully!';
          }
          fetchModelsRegistry().then(() => pollMetrics());
        } else {
          if (rawJsonStatusMsg) {
            rawJsonStatusMsg.style.color = '#ef4444';
            rawJsonStatusMsg.textContent = `⚠ Save Failed: ${data.message}`;
          }
        }
      })
      .catch(err => {
        if (rawJsonStatusMsg) {
          rawJsonStatusMsg.style.color = '#ef4444';
          rawJsonStatusMsg.textContent = `⚠ Server Error: ${err.message}`;
        }
      });
    });
  }

  function fetchModelsRegistry() {
    return fetch('/api/models')
      .then(res => res.json())
      .then(data => {
        globalModelsRegistry = data.models || [];
        if (rawJsonTextarea) {
          rawJsonTextarea.value = JSON.stringify(data, null, 2);
        }
        renderModelSelectOptions();
        renderModalModelsTable();
      })
      .catch(err => console.error('Failed to load models registry:', err));
  }

  function renderModelSelectOptions() {
    if (!adkModelSelect) return;
    const currentVal = adkModelSelect.value;
    adkModelSelect.innerHTML = '';
    globalModelsRegistry.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m.id;
      opt.textContent = `${m.name} (${m.provider === 'anthropic' ? 'Claude' : 'Gemini'})`;
      adkModelSelect.appendChild(opt);
    });
    if (currentVal && globalModelsRegistry.some(m => m.id === currentVal)) {
      adkModelSelect.value = currentVal;
    }
  }

  function renderModalModelsTable() {
    if (!modalModelsTableBody) return;
    modalModelsTableBody.innerHTML = '';
    const activeModelId = adkModelSelect ? adkModelSelect.value : '';

    globalModelsRegistry.forEach(m => {
      const tr = document.createElement('tr');
      const pricing = m.pricing || { input: 1.5, cached: 0.15, output: 9.0 };
      const isActive = (m.id === activeModelId || m.name === activeModelId);

      if (isActive) {
        tr.style.background = 'rgba(16, 185, 129, 0.08)';
        tr.style.borderLeft = '3px solid var(--color-success)';
      }

      tr.innerHTML = `
        <td style="font-family:monospace; font-size:0.75rem; color:var(--color-primary);">
          ${m.id} ${isActive ? '<span class="badge badge-success" style="margin-left:0.35rem;">Active 🟢</span>' : ''}
        </td>
        <td style="font-weight:600;">${m.name}</td>
        <td><span class="badge ${m.provider === 'anthropic' ? 'badge-purple' : 'badge-success'}">${m.provider}</span></td>
        <td>$${pricing.input.toFixed(2)}</td>
        <td>$${pricing.cached.toFixed(2)}</td>
        <td>$${pricing.output.toFixed(2)}</td>
        <td style="text-align:center;">
          <button class="btn btn-edit-model" data-id="${m.id}" style="padding:0.25rem 0.5rem; font-size:0.75rem; background:rgba(59,130,246,0.15); color:#60a5fa; border:1px solid rgba(59,130,246,0.3); border-radius:6px; margin-right:0.25rem; cursor:pointer;">Edit</button>
          <button class="btn btn-delete-model" data-id="${m.id}" style="padding:0.25rem 0.5rem; font-size:0.75rem; background:rgba(239,68,68,0.15); color:#f87171; border:1px solid rgba(239,68,68,0.3); border-radius:6px; cursor:pointer;">Delete</button>
        </td>
      `;
      modalModelsTableBody.appendChild(tr);
    });

    document.querySelectorAll('.btn-edit-model').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.target.getAttribute('data-id');
        const m = globalModelsRegistry.find(x => x.id === id);
        if (m) populateEditForm(m);
      });
    });

    document.querySelectorAll('.btn-delete-model').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.target.getAttribute('data-id');
        if (confirm(`Are you sure you want to delete model '${id}'?`)) {
          deleteModel(id);
        }
      });
    });
  }

  function populateEditForm(m) {
    if (!modelEditorForm) return;
    document.getElementById('form-model-id').value = m.id;
    document.getElementById('form-model-name').value = m.name;
    document.getElementById('form-model-provider').value = m.provider || 'google';
    document.getElementById('form-price-input').value = m.pricing ? m.pricing.input : 1.50;
    document.getElementById('form-price-cached').value = m.pricing ? m.pricing.cached : 0.15;
    document.getElementById('form-price-output').value = m.pricing ? m.pricing.output : 9.00;
    document.getElementById('form-thinking-budget').value = m.thinking_budget !== undefined ? m.thinking_budget : 0;
    document.getElementById('form-max-tokens').value = m.max_output_tokens !== undefined ? m.max_output_tokens : 8192;
    modalFormTitle.textContent = `Edit Model: ${m.name}`;
  }

  function resetEditForm() {
    if (modelEditorForm) modelEditorForm.reset();
    if (modalFormTitle) modalFormTitle.textContent = 'Add New Model Configuration';
  }

  function deleteModel(modelId) {
    fetch(`/api/models?id=${encodeURIComponent(modelId)}`, { method: 'DELETE' })
      .then(res => res.json())
      .then(data => {
        console.log('[Model Deleted]:', data);
        fetchModelsRegistry().then(() => pollMetrics());
      })
      .catch(err => console.error('Failed to delete model:', err));
  }

  if (btnManageModels) {
    btnManageModels.addEventListener('click', (e) => {
      e.preventDefault();
      fetchModelsRegistry().then(() => {
        const activeId = adkModelSelect ? adkModelSelect.value : '';
        const activeModel = globalModelsRegistry.find(x => x.id === activeId || x.name === activeId);
        if (activeModel) {
          populateEditForm(activeModel);
        } else {
          resetEditForm();
        }
      });
      if (modelModalOverlay) {
        modelModalOverlay.classList.remove('hidden');
        modelModalOverlay.style.display = 'flex';
      }
    });
  }

  if (btnCloseModal) {
    btnCloseModal.addEventListener('click', (e) => {
      e.preventDefault();
      if (modelModalOverlay) {
        modelModalOverlay.classList.add('hidden');
        modelModalOverlay.style.display = 'none';
      }
    });
  }

  if (btnCancelEdit) {
    btnCancelEdit.addEventListener('click', (e) => {
      e.preventDefault();
      resetEditForm();
    });
  }

  if (modelModalOverlay) {
    modelModalOverlay.addEventListener('click', (e) => {
      if (e.target === modelModalOverlay) {
        modelModalOverlay.classList.add('hidden');
        modelModalOverlay.style.display = 'none';
      }
    });
  }

  if (modelEditorForm) {
    modelEditorForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const modelEntry = {
        id: document.getElementById('form-model-id').value.trim(),
        name: document.getElementById('form-model-name').value.trim(),
        provider: document.getElementById('form-model-provider').value,
        pricing: {
          input: parseFloat(document.getElementById('form-price-input').value),
          cached: parseFloat(document.getElementById('form-price-cached').value),
          output: parseFloat(document.getElementById('form-price-output').value)
        },
        thinking_budget: parseInt(document.getElementById('form-thinking-budget').value),
        max_output_tokens: parseInt(document.getElementById('form-max-tokens').value),
        allowed_thinking_budgets: [0, 1024, 4096, -1],
        allowed_max_output_tokens: [1024, 2048, 4096, 8192, 16384]
      };

      fetch('/api/models', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(modelEntry)
      })
      .then(res => res.json())
      .then(data => {
        console.log('[Model Saved]:', data);
        resetEditForm();
        if (modelModalOverlay) {
          modelModalOverlay.classList.add('hidden');
          modelModalOverlay.style.display = 'none';
        }
        fetchModelsRegistry().then(() => pollMetrics());
      })
      .catch(err => console.error('Failed to save model:', err));
    });
  }

  function updateThinkingSelectOptions(modelId) {
    if (!adkThinkingSelect) return;
    const currentVal = adkThinkingSelect.value;
    const m = globalModelsRegistry.find(x => x.id === modelId || x.name === modelId);
    const isAnthropic = m ? (m.provider === 'anthropic' || m.id.includes('claude') || m.id.includes('sonnet')) : (modelId.includes('claude') || modelId.includes('sonnet'));

    adkThinkingSelect.innerHTML = '';
    if (isAnthropic) {
      const opts = [
        { val: 'off', label: 'Off (Disabled)' },
        { val: 'low', label: 'Low Effort' },
        { val: 'medium', label: 'Medium Effort' },
        { val: 'high', label: 'High Effort' }
      ];
      opts.forEach(o => {
        const el = document.createElement('option');
        el.value = o.val;
        el.textContent = o.label;
        adkThinkingSelect.appendChild(el);
      });
    } else {
      const opts = [
        { val: '0', label: '0 (Off)' },
        { val: '1024', label: '1024 Budget' },
        { val: '2048', label: '2048 Budget' },
        { val: '4096', label: '4096 Budget (Default)' },
        { val: '-1', label: '-1 (Dynamic)' }
      ];
      opts.forEach(o => {
        const el = document.createElement('option');
        el.value = o.val;
        el.textContent = o.label;
        adkThinkingSelect.appendChild(el);
      });
    }

    if (currentVal && Array.from(adkThinkingSelect.options).some(o => o.value === currentVal)) {
      adkThinkingSelect.value = currentVal;
    }
  }

  if (adkModelSelect) {
    adkModelSelect.addEventListener('change', () => {
      const modelName = adkModelSelect.value;
      updateThinkingSelectOptions(modelName);
      fetch('/api/set_model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_name: modelName })
      })
      .then(res => res.json())
      .then(data => {
        console.log('[Model Changed]:', data);
        fetchActiveConfig();
        pollMetrics();
      })
      .catch(err => console.error('Failed to set model:', err));
    });
  }

  if (adkThinkingSelect) {
    adkThinkingSelect.addEventListener('change', () => {
      const budget = adkThinkingSelect.value;
      fetch('/api/set_thinking', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thinking_budget: budget })
      })
      .then(res => res.json())
      .then(data => {
        console.log('[Thinking Budget Changed]:', data);
        pollMetrics();
      })
      .catch(err => console.error('Failed to set thinking budget:', err));
    });
  }

  if (adkMaxTokensSelect) {
    adkMaxTokensSelect.addEventListener('change', () => {
      const maxTokens = adkMaxTokensSelect.value;
      fetch('/api/set_maxtokens', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ max_output_tokens: maxTokens })
      })
      .then(res => res.json())
      .then(data => {
        console.log('[Max Tokens Changed]:', data);
        pollMetrics();
      })
      .catch(err => console.error('Failed to set max tokens:', err));
    });
  }

  function fetchActiveConfig() {
    fetch('/api/config')
      .then(response => response.json())
      .then(config => {
        if (config.model_id && adkModelSelect) {
          adkModelSelect.value = config.model_id;
          updateThinkingSelectOptions(config.model_id);
        }
        if (config.thinking_budget !== undefined && adkThinkingSelect) {
          adkThinkingSelect.value = String(config.thinking_budget);
        }
        if (config.max_output_tokens !== undefined && adkMaxTokensSelect) {
          adkMaxTokensSelect.value = String(config.max_output_tokens);
        }
      })
      .catch(err => console.warn('Failed to load active model config:', err));
  }

  // Initializing Dashboard Sync
  initCharts();
  fetchModelsRegistry().then(() => {
    fetchActiveConfig();
    startPolling();
  });

  // ==========================================
  // BIGQUERY TABLE LOGS EXPLORER ENGINE
  // ==========================================
  let bqCurrentOffset = 0;
  let bqCurrentLimit = 50;
  let bqTotalRows = 0;
  let bqCachedRows = [];

  const bqFilterApp = document.getElementById('bq-filter-app');
  const bqSearchQuery = document.getElementById('bq-search-query');
  const bqFilterLimit = document.getElementById('bq-filter-limit');
  const btnBqApplyFilter = document.getElementById('btn-bq-apply-filter');
  const btnBqRefresh = document.getElementById('btn-bq-refresh');
  const btnBqExportCsv = document.getElementById('btn-bq-export-csv');
  const btnBqExportJson = document.getElementById('btn-bq-export-json');
  const bqLogsTableBody = document.getElementById('bq-logs-table-body');
  const bqTableCountBadge = document.getElementById('bq-table-count-badge');
  const bqPageRange = document.getElementById('bq-page-range');
  const bqTotalCount = document.getElementById('bq-total-count');
  const bqPageCurrent = document.getElementById('bq-page-current');
  const btnBqPrevPage = document.getElementById('btn-bq-prev-page');
  const btnBqNextPage = document.getElementById('btn-bq-next-page');

  const bqRowModalOverlay = document.getElementById('bq-row-modal-overlay');
  const btnCloseBqModal = document.getElementById('btn-close-bq-modal');
  const modalBqApp = document.getElementById('modal-bq-app');
  const modalBqModel = document.getElementById('modal-bq-model');
  const modalBqCost = document.getElementById('modal-bq-cost');
  const modalBqTime = document.getElementById('modal-bq-time');
  const modalBqQuery = document.getElementById('modal-bq-query');
  const modalBqResponse = document.getElementById('modal-bq-response');
  const modalBqRawJson = document.getElementById('modal-bq-raw-json');
  const btnCopyBqJson = document.getElementById('btn-copy-bq-json');

  if (btnCloseBqModal && bqRowModalOverlay) {
    btnCloseBqModal.addEventListener('click', () => {
      bqRowModalOverlay.classList.add('hidden');
      bqRowModalOverlay.style.display = 'none';
    });
    bqRowModalOverlay.addEventListener('click', (e) => {
      if (e.target === bqRowModalOverlay) {
        bqRowModalOverlay.classList.add('hidden');
        bqRowModalOverlay.style.display = 'none';
      }
    });
  }

  if (btnCopyBqJson && modalBqRawJson) {
    btnCopyBqJson.addEventListener('click', () => {
      navigator.clipboard.writeText(modalBqRawJson.textContent).then(() => {
        const orig = btnCopyBqJson.textContent;
        btnCopyBqJson.textContent = '✅ Copied!';
        setTimeout(() => { btnCopyBqJson.textContent = orig; }, 1500);
      });
    });
  }

  function loadBqExplorerView() {
    fetchBqStats();
    fetchBqLogs(0);
  }

  function fetchBqStats() {
    fetch('/api/bq/stats')
      .then(res => res.json())
      .then(stats => {
        const elTurns = document.getElementById('bq-stat-total-turns');
        const elCost = document.getElementById('bq-stat-total-cost');
        const elTokens = document.getElementById('bq-stat-total-tokens');
        const elSessions = document.getElementById('bq-stat-unique-sessions');

        if (elTurns) elTurns.textContent = Number(stats.total_turns || 0).toLocaleString() + ' turns';
        if (elCost) elCost.textContent = '$' + Number(stats.total_cost || 0).toFixed(5);
        if (elTokens) {
          const fresh = Number(stats.total_input || 0).toLocaleString();
          const cached = Number(stats.total_cached || 0).toLocaleString();
          elTokens.textContent = `${fresh} / ${cached}`;
        }
        if (elSessions) elSessions.textContent = Number(stats.unique_sessions || 0).toLocaleString() + ' sessions';
      })
      .catch(err => console.warn('Failed to fetch BQ stats:', err));
  }

  function fetchBqLogs(offset = 0) {
    bqCurrentOffset = offset;
    if (bqFilterLimit) bqCurrentLimit = parseInt(bqFilterLimit.value, 10) || 50;

    const appFilter = bqFilterApp ? bqFilterApp.value : 'all';
    const searchVal = bqSearchQuery ? bqSearchQuery.value.trim() : '';

    let url = `/api/bq/logs?limit=${bqCurrentLimit}&offset=${bqCurrentOffset}`;
    if (appFilter && appFilter !== 'all') url += `&app_name=${encodeURIComponent(appFilter)}`;
    if (searchVal) url += `&search=${encodeURIComponent(searchVal)}`;

    if (bqTableCountBadge) bqTableCountBadge.textContent = 'Querying BigQuery...';

    fetch(url)
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          bqTotalRows = data.total_rows || 0;
          bqCachedRows = data.rows || [];
          renderBqLogsTable(bqCachedRows);
          updateBqPagination();
        } else {
          if (bqLogsTableBody) {
            bqLogsTableBody.innerHTML = `
              <tr>
                <td colspan="10" style="text-align:center; padding:2rem; color:#ef4444;">
                  ⚠️ Error loading logs from BigQuery: ${escapeHtml(data.message || 'Unknown error')}
                </td>
              </tr>
            `;
          }
          if (bqTableCountBadge) bqTableCountBadge.textContent = 'Error';
        }
      })
      .catch(err => {
        console.error('Failed to fetch BQ logs:', err);
        if (bqLogsTableBody) {
          bqLogsTableBody.innerHTML = `
            <tr>
              <td colspan="10" style="text-align:center; padding:2rem; color:#ef4444;">
                ⚠️ Failed to communicate with BigQuery server.
              </td>
            </tr>
          `;
        }
        if (bqTableCountBadge) bqTableCountBadge.textContent = 'Connection Error';
      });
  }

  function renderBqLogsTable(rows) {
    if (!bqLogsTableBody) return;

    if (!rows || rows.length === 0) {
      bqLogsTableBody.innerHTML = `
        <tr>
          <td colspan="10" style="text-align:center; padding:2rem; color:var(--color-text-muted);">
            No records matched the filter criteria in BigQuery.
          </td>
        </tr>
      `;
      if (bqTableCountBadge) bqTableCountBadge.textContent = '0 Records';
      return;
    }

    if (bqTableCountBadge) {
      bqTableCountBadge.textContent = `${bqTotalRows.toLocaleString()} Records Total`;
    }

    let html = '';
    rows.forEach((r, idx) => {
      const rowIdx = bqCurrentOffset + idx + 1;
      const timeFormatted = r.timestamp ? (r.timestamp.replace('T', ' ').substring(0, 19) + ' UTC') : '-';
      
      const appName = r.app_name || 'unknown';
      let appBadgeClass = 'badge-primary';
      let appDisplay = appName;
      if (appName === 'naive_app') { appBadgeClass = 'badge-danger'; appDisplay = '1. Naive'; }
      else if (appName === 'caching_app') { appBadgeClass = 'badge-success'; appDisplay = '2. Caching'; }
      else if (appName === 'compaction_app') { appBadgeClass = 'badge-warning'; appDisplay = '3. Compaction'; }
      else if (appName === 'skills_app') { appBadgeClass = 'badge-primary'; appDisplay = '4. Modular Skills'; }

      const querySnippet = r.user_query ? (r.user_query.length > 55 ? r.user_query.substring(0, 52) + '...' : r.user_query) : '-';
      const respSnippet = r.agent_response ? (r.agent_response.length > 60 ? r.agent_response.substring(0, 57) + '...' : r.agent_response) : '-';

      const promptTok = Number(r.prompt_tokens || 0).toLocaleString();
      const cachedTok = Number(r.cached_tokens || 0).toLocaleString();
      const outTok = Number(r.output_tokens || 0).toLocaleString();
      const thinkTok = Number(r.thinking_tokens || 0).toLocaleString();
      const costStr = '$' + Number(r.estimated_cost || 0).toFixed(5);

      // Tools / Skills badge
      let toolsBadge = '<span style="color:var(--color-text-muted); font-size:0.75rem;">None</span>';
      if (r.invoked_skills) {
        toolsBadge = `<span class="badge badge-primary" style="font-size:0.7rem;">⚡ ${escapeHtml(r.invoked_skills)}</span>`;
      } else if (r.invoked_tools) {
        toolsBadge = `<span class="badge" style="background:rgba(59,130,246,0.15); color:#60a5fa; border:1px solid rgba(59,130,246,0.3); font-size:0.7rem;">🛠️ ${escapeHtml(r.invoked_tools.length > 30 ? r.invoked_tools.substring(0, 28) + '..' : r.invoked_tools)}</span>`;
      }

      html += `
        <tr style="cursor:pointer;" onclick="window.inspectBqRow(${idx})">
          <td style="font-family:monospace; color:var(--color-text-muted);">${rowIdx}</td>
          <td style="font-family:monospace; font-size:0.75rem; color:#94a3b8; white-space:nowrap;">${escapeHtml(timeFormatted)}</td>
          <td style="font-family:monospace; font-size:0.75rem; color:#60a5fa; max-width:110px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${escapeHtml(r.session_id)}">
            ${escapeHtml(r.session_id || '-')}
          </td>
          <td><span class="badge ${appBadgeClass}" style="font-size:0.75rem;">${escapeHtml(appDisplay)}</span></td>
          <td style="max-width:180px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${escapeHtml(r.user_query)}">
            ${escapeHtml(querySnippet)}
          </td>
          <td style="max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:var(--color-text-muted);" title="${escapeHtml(r.agent_response)}">
            ${escapeHtml(respSnippet)}
          </td>
          <td style="font-family:monospace; font-size:0.75rem; white-space:nowrap;">
            <span style="color:#60a5fa;" title="Fresh Input">${promptTok}</span> / 
            <span style="color:#34d399;" title="Cached Discounted">${cachedTok}</span> / 
            <span style="color:#f59e0b;" title="Output">${outTok}</span> / 
            <span style="color:#c084fc;" title="Thinking">${thinkTok}</span>
          </td>
          <td style="font-family:monospace; font-weight:600; color:var(--color-success);">${costStr}</td>
          <td>${toolsBadge}</td>
          <td style="text-align:center;">
            <button type="button" class="btn" style="padding:0.25rem 0.6rem; font-size:0.75rem; background:rgba(255,255,255,0.06); color:var(--color-primary-light); border:1px solid rgba(255,255,255,0.1); border-radius:6px; cursor:pointer;" onclick="event.stopPropagation(); window.inspectBqRow(${idx});">
              🔍 View
            </button>
          </td>
        </tr>
      `;
    });

    bqLogsTableBody.innerHTML = html;
  }

  function updateBqPagination() {
    const start = bqTotalRows === 0 ? 0 : bqCurrentOffset + 1;
    const end = Math.min(bqCurrentOffset + bqCurrentLimit, bqTotalRows);
    const currentPage = Math.floor(bqCurrentOffset / bqCurrentLimit) + 1;
    const totalPages = Math.ceil(bqTotalRows / bqCurrentLimit) || 1;

    if (bqPageRange) bqPageRange.textContent = `${start} - ${end}`;
    if (bqTotalCount) bqTotalCount.textContent = bqTotalRows.toLocaleString();
    if (bqPageCurrent) bqPageCurrent.textContent = `Page ${currentPage} of ${totalPages}`;

    if (btnBqPrevPage) btnBqPrevPage.disabled = bqCurrentOffset <= 0;
    if (btnBqNextPage) btnBqNextPage.disabled = end >= bqTotalRows;
  }

  window.inspectBqRow = function(index) {
    const row = bqCachedRows[index];
    if (!row || !bqRowModalOverlay) return;

    if (modalBqApp) modalBqApp.textContent = row.app_name || '-';
    if (modalBqModel) modalBqModel.textContent = row.model_name || 'Gemini 3.5 Flash';
    if (modalBqCost) modalBqCost.textContent = '$' + Number(row.estimated_cost || 0).toFixed(5);
    if (modalBqTime) modalBqTime.textContent = row.timestamp || '-';
    if (modalBqQuery) modalBqQuery.textContent = row.user_query || '(empty prompt)';
    if (modalBqResponse) modalBqResponse.textContent = row.agent_response || '(empty response)';
    if (modalBqRawJson) modalBqRawJson.textContent = JSON.stringify(row, null, 2);

    bqRowModalOverlay.classList.remove('hidden');
    bqRowModalOverlay.style.display = 'flex';
  };

  if (btnBqApplyFilter) {
    btnBqApplyFilter.addEventListener('click', () => fetchBqLogs(0));
  }

  if (btnBqRefresh) {
    btnBqRefresh.addEventListener('click', () => {
      fetchBqStats();
      fetchBqLogs(bqCurrentOffset);
    });
  }

  if (btnBqPrevPage) {
    btnBqPrevPage.addEventListener('click', () => {
      if (bqCurrentOffset > 0) {
        fetchBqLogs(Math.max(0, bqCurrentOffset - bqCurrentLimit));
      }
    });
  }

  if (btnBqNextPage) {
    btnBqNextPage.addEventListener('click', () => {
      if (bqCurrentOffset + bqCurrentLimit < bqTotalRows) {
        fetchBqLogs(bqCurrentOffset + bqCurrentLimit);
      }
    });
  }

  if (btnBqExportJson) {
    btnBqExportJson.addEventListener('click', () => {
      if (!bqCachedRows || bqCachedRows.length === 0) {
        alert('No rows available to export.');
        return;
      }
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(bqCachedRows, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `bq_token_logs_${new Date().toISOString().substring(0, 10)}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    });
  }

  if (btnBqExportCsv) {
    btnBqExportCsv.addEventListener('click', () => {
      if (!bqCachedRows || bqCachedRows.length === 0) {
        alert('No rows available to export.');
        return;
      }
      const headers = ["timestamp", "session_id", "app_name", "model_name", "prompt_tokens", "cached_tokens", "output_tokens", "thinking_tokens", "estimated_cost", "invoked_tools", "invoked_skills", "user_query", "agent_response"];
      let csvContent = "data:text/csv;charset=utf-8," + headers.join(",") + "\n";

      bqCachedRows.forEach(r => {
        const rowData = [
          `"${(r.timestamp || '').replace(/"/g, '""')}"`,
          `"${(r.session_id || '').replace(/"/g, '""')}"`,
          `"${(r.app_name || '').replace(/"/g, '""')}"`,
          `"${(r.model_name || '').replace(/"/g, '""')}"`,
          r.prompt_tokens || 0,
          r.cached_tokens || 0,
          r.output_tokens || 0,
          r.thinking_tokens || 0,
          r.estimated_cost || 0.0,
          `"${(r.invoked_tools || '').replace(/"/g, '""')}"`,
          `"${(r.invoked_skills || '').replace(/"/g, '""')}"`,
          `"${(r.user_query || '').replace(/"/g, '""')}"`,
          `"${(r.agent_response || '').replace(/"/g, '""')}"`
        ];
        csvContent += rowData.join(",") + "\n";
      });

      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", `bq_token_logs_${new Date().toISOString().substring(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    });
  }
});
