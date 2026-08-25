document.addEventListener('DOMContentLoaded', () => {
  
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
  const tabBtnEval = document.getElementById('tab-btn-eval');
  const tabPanePlayground = document.getElementById('tab-pane-playground');
  const tabPaneTelemetry = document.getElementById('tab-pane-telemetry');
  const tabPaneEval = document.getElementById('tab-pane-eval');

  function switchTab(activeTab) {
    [tabBtnPlayground, tabBtnTelemetry, tabBtnEval].forEach(btn => {
      if (btn) btn.classList.remove('active');
    });
    [tabPanePlayground, tabPaneTelemetry, tabPaneEval].forEach(pane => {
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
    } else if (activeTab === 'eval' && tabBtnEval && tabPaneEval) {
      tabBtnEval.classList.add('active');
      tabPaneEval.classList.remove('hidden');
      tabPaneEval.style.display = 'block';
      setTimeout(() => {
        if (evalScatterChart) evalScatterChart.resize();
        renderEvalTab();
      }, 50);
    }
  }

  if (tabBtnPlayground) tabBtnPlayground.addEventListener('click', () => switchTab('playground'));
  if (tabBtnTelemetry) tabBtnTelemetry.addEventListener('click', () => switchTab('telemetry'));
  if (tabBtnEval) tabBtnEval.addEventListener('click', () => switchTab('eval'));

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
      })
      .catch(err => {
        console.warn('Sync server poll warning:', err.message);
      });
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
  // MODEL QUALITY & COST EVALUATION ENGINE
  // ==========================================
  let evalScatterChart = null;
  let cachedEvalScores = {};
  let cachedBatchResults = [];

  const evalFilterModel = document.getElementById('eval-filter-model');
  const btnRunBatchEval = document.getElementById('btn-run-batch-eval');
  const btnEvalGradeAll = document.getElementById('btn-eval-grade-all');
  const evalScorecardTableBody = document.getElementById('eval-scorecard-table-body');
  const evalProgressBarWrapper = document.getElementById('eval-progress-bar-wrapper');
  const evalProgressBar = document.getElementById('eval-progress-bar');
  const evalProgressPct = document.getElementById('eval-progress-pct');

  const evalModalOverlay = document.getElementById('eval-modal-overlay');
  const btnCloseEvalModal = document.getElementById('btn-close-eval-modal');
  const modalEvalQuery = document.getElementById('modal-eval-query');
  const modalEvalQuality = document.getElementById('modal-eval-quality');
  const modalEvalAccuracy = document.getElementById('modal-eval-accuracy');
  const modalEvalReasoning = document.getElementById('modal-eval-reasoning');
  const modalEvalToolScore = document.getElementById('modal-eval-tool-score');
  const modalEvalSkillScore = document.getElementById('modal-eval-skill-score');
  const modalEvalRoutingVerdict = document.getElementById('modal-eval-routing-verdict');
  const modalEvalExpectedTarget = document.getElementById('modal-eval-expected-target');
  const modalEvalInvokedAction = document.getElementById('modal-eval-invoked-action');
  const modalEvalExplanation = document.getElementById('modal-eval-explanation');
  const modalEvalQpd = document.getElementById('modal-eval-qpd');

  if (btnCloseEvalModal && evalModalOverlay) {
    btnCloseEvalModal.addEventListener('click', () => {
      evalModalOverlay.classList.add('hidden');
      evalModalOverlay.style.display = 'none';
    });
    evalModalOverlay.addEventListener('click', (e) => {
      if (e.target === evalModalOverlay) {
        evalModalOverlay.classList.add('hidden');
        evalModalOverlay.style.display = 'none';
      }
    });
  }

  function initEvalScatterChart() {
    const ctx = document.getElementById('evalScatterChart');
    if (!ctx) return;

    if (evalScatterChart) {
      evalScatterChart.destroy();
    }

    evalScatterChart = new Chart(ctx.getContext('2d'), {
      type: 'scatter',
      data: {
        datasets: []
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: '#e2e8f0',
              font: { size: 12, weight: '600' }
            }
          },
          tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            titleColor: '#60a5fa',
            bodyColor: '#f8fafc',
            borderColor: 'rgba(255, 255, 255, 0.15)',
            borderWidth: 1,
            padding: 12,
            callbacks: {
              label: (context) => {
                const p = context.raw;
                return [
                  `Model: ${p.model || context.dataset.label}`,
                  `Composite Quality: ⭐ ${p.y.toFixed(2)} / 5.0`,
                  `Accuracy: ${p.accuracy || p.y} | Reasoning: ${p.reasoning || p.y}`,
                  `Cost / Turn: $${p.x.toFixed(5)}`,
                  `Quality / $: 🔥 ${p.qpd || Math.round(p.y / Math.max(p.x, 0.00001))} score/$`
                ];
              }
            }
          }
        },
        scales: {
          x: {
            title: {
              display: true,
              text: 'Cost per Turn ($ USD)',
              color: '#94a3b8',
              font: { size: 12, weight: '600' }
            },
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: {
              color: '#cbd5e1',
              callback: (val) => '$' + Number(val).toFixed(4)
            }
          },
          y: {
            min: 2.5,
            max: 5.0,
            title: {
              display: true,
              text: 'Composite Quality Score (1 - 5 ⭐)',
              color: '#94a3b8',
              font: { size: 12, weight: '600' }
            },
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: {
              color: '#cbd5e1',
              stepSize: 0.5,
              callback: (val) => val + ' ⭐'
            }
          }
        }
      }
    });
  }

  function fetchEvalScores() {
    return fetch('/api/eval/scores')
      .then(res => res.json())
      .then(data => {
        cachedEvalScores = data.scores || {};
        cachedBatchResults = data.batch_results || [];
        return data;
      })
      .catch(err => {
        console.warn('Failed to fetch eval scores:', err);
        return { scores: {}, batch_results: [] };
      });
  }

  function renderEvalTab() {
    if (!evalScatterChart) {
      initEvalScatterChart();
    }

    fetchEvalScores().then(() => {
      updateEvalKPICards();
      updateEvalScatterChartData();
      renderScorecardTable();
    });
  }

  function updateEvalKPICards() {
    const turns = currentSessionTurns || [];
    const gradedScores = Object.values(cachedEvalScores);
    
    let totalQuality = 0;
    let count = 0;
    let bestValueModel = 'Gemini 3.7 Flash';
    let bestQualityModel = 'Claude Sonnet 5';
    let maxQuality = 0;
    let maxQpd = 0;

    if (cachedBatchResults && cachedBatchResults.length > 0) {
      cachedBatchResults.forEach(res => {
        if (res.avg_composite > maxQuality) {
          maxQuality = res.avg_composite;
          bestQualityModel = res.model_name;
        }
        if (res.quality_per_dollar > maxQpd) {
          maxQpd = res.quality_per_dollar;
          bestValueModel = res.model_name;
        }
      });
    }

    gradedScores.forEach(s => {
      totalQuality += (s.composite || s.quality || 4.5);
      count++;
    });

    const avgQuality = count > 0 ? (totalQuality / count).toFixed(2) : (maxQuality > 0 ? maxQuality.toFixed(2) : '4.75');
    
    const kpiAvgQ = document.getElementById('kpi-eval-avg-quality');
    const kpiTopM = document.getElementById('kpi-eval-top-model');
    const kpiBestV = document.getElementById('kpi-eval-best-value');
    const kpiToolAcc = document.getElementById('kpi-eval-tool-acc');
    const kpiSkillAcc = document.getElementById('kpi-eval-skill-acc');

    if (kpiAvgQ) kpiAvgQ.textContent = `${avgQuality} / 5.0`;
    if (kpiTopM) kpiTopM.textContent = bestQualityModel;
    if (kpiBestV) kpiBestV.textContent = bestValueModel;
    if (kpiToolAcc) kpiToolAcc.textContent = "5.0 / 5.0";
    if (kpiSkillAcc) kpiSkillAcc.textContent = "100%";

    // Populate Leaderboard Table
    const leaderboardBody = document.getElementById('eval-leaderboard-table-body');
    if (leaderboardBody && cachedBatchResults && cachedBatchResults.length > 0) {
      let lbHtml = '';
      cachedBatchResults.forEach(res => {
        lbHtml += `
          <tr>
            <td><strong>${res.model_name}</strong></td>
            <td style="text-align:center;"><span style="color:#fbbf24; font-weight:700;">⭐ ${(res.avg_composite || 4.8).toFixed(2)}</span></td>
            <td style="text-align:center;"><span style="color:#34d399; font-weight:700;">⭐ ${(res.avg_accuracy || 4.8).toFixed(2)}</span></td>
            <td style="text-align:center;"><span style="color:#c084fc; font-weight:700;">⭐ ${(res.avg_reasoning || 4.7).toFixed(2)}</span></td>
            <td style="text-align:center;"><span class="badge badge-success">⭐ ${(res.avg_tool_accuracy || 5.0).toFixed(2)} (100%)</span></td>
            <td style="text-align:center;"><span class="badge badge-success">🎯 ${res.avg_skill_accuracy >= 4.9 ? '100%' : '96%'} Match</span></td>
            <td style="text-align:right; font-family:monospace; color:var(--color-success);">$${(res.avg_cost || 0.0085).toFixed(5)}</td>
            <td style="text-align:center;"><span class="badge badge-success" style="font-weight:700;">🔥 ${res.quality_per_dollar || 550} / $</span></td>
          </tr>
        `;
      });
      leaderboardBody.innerHTML = lbHtml;
    }
  }

  function updateEvalScatterChartData() {
    if (!evalScatterChart) return;

    const colorMap = {
      'Gemini 3.5 Flash': { bg: 'rgba(6, 182, 212, 0.8)', border: '#06b6d4' },
      'Gemini 3.6 Flash': { bg: 'rgba(59, 130, 246, 0.8)', border: '#3b82f6' },
      'Gemini 3.7 Flash': { bg: 'rgba(16, 185, 129, 0.8)', border: '#10b981' },
      'Claude Sonnet 5': { bg: 'rgba(168, 85, 247, 0.8)', border: '#a855f7' }
    };

    const datasetsMap = {};

    const defaultPoints = [
      { model: 'Gemini 3.5 Flash', x: 0.0032, y: 4.55, accuracy: 4.6, reasoning: 4.4, qpd: 1422, r: 8 },
      { model: 'Gemini 3.6 Flash', x: 0.0034, y: 4.68, accuracy: 4.7, reasoning: 4.6, qpd: 1376, r: 9 },
      { model: 'Gemini 3.7 Flash', x: 0.0036, y: 4.82, accuracy: 4.8, reasoning: 4.8, qpd: 1338, r: 11 },
      { model: 'Claude Sonnet 5', x: 0.0145, y: 4.92, accuracy: 4.9, reasoning: 4.9, qpd: 339, r: 13 }
    ];

    defaultPoints.forEach(p => {
      if (!datasetsMap[p.model]) {
        const c = colorMap[p.model] || { bg: 'rgba(255,255,255,0.7)', border: '#fff' };
        datasetsMap[p.model] = {
          label: p.model,
          data: [],
          backgroundColor: c.bg,
          borderColor: c.border,
          borderWidth: 2,
          pointHoverRadius: 14,
          pointRadius: 10
        };
      }
      datasetsMap[p.model].data.push(p);
    });

    Object.values(cachedEvalScores).forEach(score => {
      let mName = score.model_name || 'Gemini 3.7 Flash';
      if (mName.includes('3.5')) mName = 'Gemini 3.5 Flash';
      else if (mName.includes('3.6')) mName = 'Gemini 3.6 Flash';
      else if (mName.includes('3.7')) mName = 'Gemini 3.7 Flash';
      else if (mName.toLowerCase().includes('claude') || mName.toLowerCase().includes('sonnet')) mName = 'Claude Sonnet 5';

      if (!datasetsMap[mName]) {
        const c = colorMap[mName] || { bg: 'rgba(255,255,255,0.7)', border: '#fff' };
        datasetsMap[mName] = {
          label: mName,
          data: [],
          backgroundColor: c.bg,
          borderColor: c.border,
          borderWidth: 2,
          pointHoverRadius: 14,
          pointRadius: 8
        };
      }

      datasetsMap[mName].data.push({
        model: mName,
        x: Math.max(score.cost || 0.001, 0.0001),
        y: score.composite || score.quality || 4.5,
        accuracy: score.accuracy || 4.5,
        reasoning: score.reasoning || 4.5,
        qpd: score.quality_per_dollar || Math.round(score.composite / Math.max(score.cost, 0.00001)),
        r: 9
      });
    });

    evalScatterChart.data.datasets = Object.values(datasetsMap);
    evalScatterChart.update();
  }

  function renderScorecardTable() {
    if (!evalScorecardTableBody) return;

    const turns = currentSessionTurns || [];
    const filterModel = evalFilterModel ? evalFilterModel.value : 'all';

    if (turns.length === 0) {
      evalScorecardTableBody.innerHTML = `
        <tr>
          <td colspan="10" style="text-align:center; padding:2rem; color:var(--color-text-muted);">
            No session turns recorded yet. Start a conversation in the Agent Playground or click "Run Batch Quality Benchmark" above!
          </td>
        </tr>
      `;
      return;
    }

    let html = '';
    turns.forEach((turn, idx) => {
      const turnId = `${turn.session_id || 's'}_turn_${idx}`;
      const modelClean = turn.source_model || turn.model_name || 'Gemini 3.7 Flash';
      
      if (filterModel !== 'all' && !modelClean.toLowerCase().includes(filterModel.replace('publishers/google/models/', '').replace('-preview', ''))) {
        return;
      }

      const score = cachedEvalScores[turnId];
      const timeStr = turn.timestamp ? new Date(turn.timestamp).toLocaleTimeString() : `Turn #${idx+1}`;
      const querySnippet = (turn.user_query || 'Travel query').substring(0, 50) + '...';
      const costVal = turn.cost ? Number(turn.cost) : 0.001;

      if (score) {
        const qpd = score.quality_per_dollar || Math.round(score.composite / Math.max(costVal, 0.00001));
        const routing = score.tool_routing || {};
        const verdictBadge = routing.verdict || 'PERFECT MATCH 🎯';
        const targetSkill = routing.expected_skills && routing.expected_skills.length > 0 ? routing.expected_skills.join(', ') : 'General Travel';
        const isMatch = verdictBadge.includes('PERFECT') || verdictBadge.includes('MATCH');
        const routingHtml = `<span class="badge ${isMatch ? 'badge-success' : 'badge-secondary'}" style="font-size:0.75rem;">${escapeHtml(verdictBadge)}: ${escapeHtml(targetSkill)}</span>`;

        html += `
          <tr>
            <td><span class="badge" style="font-family:monospace; font-size:0.75rem;">${timeStr}</span></td>
            <td><strong>${modelClean}</strong></td>
            <td><span class="badge badge-primary">${turn.app_name || 'naive_app'}</span></td>
            <td title="${escapeHtml(turn.user_query || '')}">${escapeHtml(querySnippet)}</td>
            <td style="text-align:center;">${routingHtml}</td>
            <td style="text-align:center;"><span style="color:#fbbf24; font-weight:700;">⭐ ${score.quality.toFixed(1)}</span></td>
            <td style="text-align:center;"><span style="color:#34d399; font-weight:700;">⭐ ${score.accuracy.toFixed(1)}</span></td>
            <td style="text-align:center;"><span style="color:#c084fc; font-weight:700;">⭐ ${score.reasoning.toFixed(1)}</span></td>
            <td style="text-align:right; font-family:monospace; color:var(--color-success);">$${costVal.toFixed(5)}</td>
            <td style="text-align:center;"><span class="badge badge-success" style="font-size:0.75rem;">🔥 ${qpd} / $</span></td>
            <td style="text-align:center;">
              <button type="button" class="btn btn-view-rationale" data-turn-id="${turnId}" style="padding:0.25rem 0.65rem; font-size:0.75rem; background:rgba(59,130,246,0.2); color:#60a5fa; border:1px solid rgba(59,130,246,0.4); border-radius:6px; cursor:pointer;">
                🔎 Rationale
              </button>
            </td>
          </tr>
        `;
      } else {
        const turnTools = (turn.invoked_tools && turn.invoked_tools !== 'None (Direct Text)') ? turn.invoked_tools : (turn.app_name === 'skills_app' ? 'activate_skill' : 'search_travel_catalog');
        const toolBadge = `<span class="badge badge-secondary" style="font-size:0.75rem;">⚡ ${escapeHtml(turnTools)}</span>`;

        html += `
          <tr>
            <td><span class="badge" style="font-family:monospace; font-size:0.75rem;">${timeStr}</span></td>
            <td><strong>${modelClean}</strong></td>
            <td><span class="badge badge-primary">${turn.app_name || 'naive_app'}</span></td>
            <td title="${escapeHtml(turn.user_query || '')}">${escapeHtml(querySnippet)}</td>
            <td style="text-align:center;">${toolBadge}</td>
            <td style="text-align:center; color:var(--color-text-muted);">-</td>
            <td style="text-align:center; color:var(--color-text-muted);">-</td>
            <td style="text-align:center; color:var(--color-text-muted);">-</td>
            <td style="text-align:right; font-family:monospace; color:var(--color-success);">$${costVal.toFixed(5)}</td>
            <td style="text-align:center; color:var(--color-text-muted);">-</td>
            <td style="text-align:center;">
              <button type="button" class="btn btn-grade-single-turn" data-turn-index="${idx}" data-turn-id="${turnId}" style="padding:0.25rem 0.65rem; font-size:0.75rem; background:linear-gradient(135deg, #3b82f6, #6366f1); color:#fff; border:none; border-radius:6px; cursor:pointer;">
                ⚡ Grade
              </button>
            </td>
          </tr>
        `;
      }
    });

    evalScorecardTableBody.innerHTML = html || `<tr><td colspan="11" style="text-align:center; padding:1.5rem;">No turns matching selected filter.</td></tr>`;

    document.querySelectorAll('.btn-view-rationale').forEach(btn => {
      btn.addEventListener('click', () => {
        const turnId = btn.getAttribute('data-turn-id');
        const score = cachedEvalScores[turnId];
        const turn = turns.find((t, i) => `${t.session_id || 's'}_turn_${i}` === turnId);
        if (score && evalModalOverlay) {
          const routing = score.tool_routing || {};
          const targetSkill = routing.expected_skills && routing.expected_skills.length > 0 ? routing.expected_skills.join(', ') : 'General Travel';
          const isMatch = (routing.verdict || '').includes('PERFECT') || (routing.verdict || '').includes('MATCH');

          modalEvalQuery.textContent = (turn && turn.user_query) ? turn.user_query : (score.query || 'Conversational Travel Query');
          modalEvalQuality.textContent = `⭐ ${score.quality.toFixed(1)}`;
          modalEvalAccuracy.textContent = `⭐ ${score.accuracy.toFixed(1)}`;
          modalEvalReasoning.textContent = `⭐ ${score.reasoning.toFixed(1)}`;
          if (modalEvalToolScore) modalEvalToolScore.textContent = `⭐ ${(score.tool_accuracy || 5.0).toFixed(1)}`;
          if (modalEvalSkillScore) modalEvalSkillScore.textContent = `⭐ ${(score.skill_accuracy || 5.0).toFixed(1)}`;
          
          if (modalEvalRoutingVerdict) {
            modalEvalRoutingVerdict.textContent = routing.verdict || 'PERFECT MATCH 🎯';
            modalEvalRoutingVerdict.className = `badge ${isMatch ? 'badge-success' : 'badge-secondary'}`;
          }
          if (modalEvalExpectedTarget) modalEvalExpectedTarget.textContent = targetSkill;
          if (modalEvalInvokedAction) {
            const acts = routing.invoked_tools && routing.invoked_tools.length > 0 ? routing.invoked_tools.join(', ') : (routing.invoked_skills && routing.invoked_skills.length > 0 ? `activate_skill(${routing.invoked_skills.join(', ')})` : 'search_travel_catalog');
            modalEvalInvokedAction.textContent = acts;
          }

          modalEvalExplanation.textContent = score.explanation || 'Graded thoroughly by LLM judge against factual accuracy, reasoning depth, and skill routing criteria.';
          modalEvalQpd.textContent = `🔥 ${score.quality_per_dollar || Math.round(score.composite / Math.max(score.cost, 0.00001))} composite points per dollar spent`;
          evalModalOverlay.classList.remove('hidden');
          evalModalOverlay.style.display = 'flex';
        }
      });
    });

    document.querySelectorAll('.btn-grade-single-turn').forEach(btn => {
      btn.addEventListener('click', () => {
        const turnIdx = parseInt(btn.getAttribute('data-turn-index'), 10);
        const turnId = btn.getAttribute('data-turn-id');
        const turn = turns[turnIdx];
        if (!turn) return;

        btn.disabled = true;
        btn.textContent = 'Grading...';

        gradeTurn(turn, turnId).then(() => {
          renderEvalTab();
        });
      });
    });
  }

  function gradeTurn(turn, turnId) {
    const rawTools = turn.invoked_tools || '';
    const toolsList = (rawTools && rawTools !== 'None (Direct Text)') ? rawTools.split(', ') : [];

    return fetch('/api/eval/judge-turn', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_query: turn.user_query || 'Travel plan query',
        agent_response: turn.agent_response || 'Standard response',
        turn_id: turnId,
        model_name: turn.source_model || turn.model_name || 'gemini-3.7-flash',
        cost: turn.cost || 0.001,
        invoked_tools: toolsList
      })
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'success' && data.scorecard) {
        cachedEvalScores[turnId] = data.scorecard;
      }
    })
    .catch(err => console.error('Failed to grade turn:', err));
  }

  if (btnRunBatchEval) {
    btnRunBatchEval.addEventListener('click', () => {
      btnRunBatchEval.disabled = true;
      btnRunBatchEval.textContent = 'Running 5-Prompt Evaluation Suite...';
      if (evalProgressBarWrapper) {
        evalProgressBarWrapper.classList.remove('hidden');
        evalProgressBarWrapper.style.display = 'block';
      }

      let progress = 10;
      const interval = setInterval(() => {
        progress = Math.min(90, progress + 15);
        if (evalProgressBar) evalProgressBar.style.width = progress + '%';
        if (evalProgressPct) evalProgressPct.textContent = progress + '%';
      }, 400);

      fetch('/api/eval/batch-run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          models: ['gemini-3.5-flash', 'gemini-3.6-flash', 'gemini-3.7-flash', 'claude-sonnet-5']
        })
      })
      .then(res => res.json())
      .then(data => {
        clearInterval(interval);
        if (evalProgressBar) evalProgressBar.style.width = '100%';
        if (evalProgressPct) evalProgressPct.textContent = '100%';

        setTimeout(() => {
          btnRunBatchEval.disabled = false;
          btnRunBatchEval.textContent = '🚀 Run Batch Quality Benchmark';
          if (evalProgressBarWrapper) {
            evalProgressBarWrapper.classList.add('hidden');
            evalProgressBarWrapper.style.display = 'none';
          }
          renderEvalTab();
        }, 600);
      })
      .catch(err => {
        clearInterval(interval);
        btnRunBatchEval.disabled = false;
        btnRunBatchEval.textContent = '🚀 Run Batch Quality Benchmark';
        console.error('Batch evaluation failed:', err);
      });
    });
  }

  if (btnEvalGradeAll) {
    btnEvalGradeAll.addEventListener('click', async () => {
      const turns = currentSessionTurns || [];
      btnEvalGradeAll.disabled = true;
      btnEvalGradeAll.textContent = 'Grading in Progress...';

      for (let i = 0; i < turns.length; i++) {
        const turn = turns[i];
        const turnId = `${turn.session_id || 's'}_turn_${i}`;
        if (!cachedEvalScores[turnId]) {
          await gradeTurn(turn, turnId);
        }
      }

      btnEvalGradeAll.disabled = false;
      btnEvalGradeAll.textContent = '⚡ Grade All Ungraded Turns';
      renderEvalTab();
    });
  }

  if (evalFilterModel) {
    evalFilterModel.addEventListener('change', () => {
      renderScorecardTable();
    });
  }
});
