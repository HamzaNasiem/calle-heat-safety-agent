"""FastAPI Webhook & REST Server for CALL-E Heat Guardian with Interactive Web Dashboard."""

import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from skills.heat_safety_dispatcher.dispatcher import (
    HeatSafetyPayload,
    CallDispatchResult,
    trigger_heat_call,
    poll_call_status,
)
from config import settings

app = FastAPI(
    title="CALL-E Heat Guardian API",
    description="Autonomous Emergency Voice Dispatcher for Workforce Heat Safety powered by CALL-E.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
def index_dashboard():
    """Interactive Mission Control Web Dashboard for testing CALL-E Voice AI."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CALL-E Heat Guardian — Voice AI Mission Control</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    @keyframes pulse-glow {
      0%, 100% { box-shadow: 0 0 15px rgba(239, 68, 68, 0.4); }
      50% { box-shadow: 0 0 25px rgba(239, 68, 68, 0.8); }
    }
    .emergency-glow { animation: pulse-glow 2s infinite; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans antialiased selection:bg-rose-500 selection:text-white">

  <!-- Top Navigation Header -->
  <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
    <div class="max-w-6xl mx-auto px-4 py-4 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-rose-500 to-amber-500 flex items-center justify-center shadow-lg shadow-rose-500/30">
          <i class="fa-solid fa-phone-volume text-white text-lg"></i>
        </div>
        <div>
          <h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            CALL-E <span class="text-rose-400">Heat Guardian</span>
            <span class="text-xs px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30 font-mono">LIVE AGENT</span>
          </h1>
          <p class="text-xs text-slate-400">Autonomous Workforce Emergency Voice Dispatcher</p>
        </div>
      </div>
      <div class="flex items-center space-x-3">
        <a href="/docs" target="_blank" class="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 border border-slate-700 transition flex items-center gap-1.5">
          <i class="fa-solid fa-book-open text-slate-400"></i> Swagger API Docs
        </a>
        <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
          CALL-E API Connected
        </div>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="max-w-6xl mx-auto px-4 py-8">
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
      
      <!-- Left Column: Dialer & Control Panel (7 cols) -->
      <div class="lg:col-span-7 space-y-6">
        
        <!-- Action Card -->
        <div class="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
          <div class="absolute top-0 right-0 w-64 h-64 bg-rose-500/5 rounded-full blur-3xl pointer-events-none"></div>

          <div class="flex items-center justify-between pb-4 border-b border-slate-800 mb-6">
            <h2 class="text-lg font-semibold text-white flex items-center gap-2">
              <i class="fa-solid fa-tower-broadcast text-rose-400"></i> Dispatch Emergency Voice Call
            </h2>
            <span class="text-xs text-slate-400 font-mono">api.heycall-e.com/v1</span>
          </div>

          <form id="dispatchForm" class="space-y-4">
            <!-- Phone & Worker Name -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1.5">Recipient Phone (E.164)</label>
                <div class="relative">
                  <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                    <i class="fa-solid fa-phone"></i>
                  </span>
                  <input type="text" id="phoneNumber" value="+923172532350" required
                    class="w-full pl-9 pr-3 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-rose-500 focus:ring-1 focus:ring-rose-500 transition font-mono">
                </div>
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1.5">Worker / Foreman Name</label>
                <div class="relative">
                  <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                    <i class="fa-solid fa-user-shield"></i>
                  </span>
                  <input type="text" id="workerName" value="Hamza (Safety Officer)" required
                    class="w-full pl-9 pr-3 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-rose-500 focus:ring-1 focus:ring-rose-500 transition">
                </div>
              </div>
            </div>

            <!-- Job Site & Temperature -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1.5">Job Site Facility</label>
                <input type="text" id="siteName" value="Downtown Los Angeles Freight Yard, CA" required
                  class="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-rose-500 focus:ring-1 focus:ring-rose-500 transition">
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1.5 flex justify-between">
                  <span>Hazard Temperature (°F)</span>
                  <span id="tempBadge" class="text-rose-400 font-bold font-mono">108.5°F</span>
                </label>
                <input type="range" id="tempRange" min="95" max="120" step="0.5" value="108.5"
                  class="w-full accent-rose-500 bg-slate-800 rounded-lg cursor-pointer h-2 mt-3">
              </div>
            </div>

            <!-- OSHA Work Rest & Water Quota -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1.5">Cal/OSHA Work/Rest Protocol</label>
                <select id="workRestRatio" class="w-full px-3 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-rose-500 transition">
                  <option value="15 min work / 45 min rest">Extreme: 15m Work / 45m Rest (Mandatory)</option>
                  <option value="30 min work / 30 min rest">Elevated: 30m Work / 30m Rest</option>
                  <option value="45 min work / 15 min rest">Moderate: 45m Work / 15m Rest</option>
                  <option value="STOP ALL OUTDOOR WORK">Emergency: FULL STOP WORK</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1.5">Cooling Refuge Sector</label>
                <input type="text" id="coolingRefuge" value="North-East Shaded Canopy (Sector B)"
                  class="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-rose-500 transition">
              </div>
            </div>

            <!-- Submit Button -->
            <button type="submit" id="btnTrigger"
              class="w-full mt-4 py-3.5 px-6 rounded-xl bg-gradient-to-r from-rose-600 via-rose-500 to-amber-600 text-white font-bold text-sm tracking-wide shadow-lg shadow-rose-600/30 hover:shadow-rose-600/50 hover:brightness-110 active:scale-[0.99] transition duration-200 flex items-center justify-center gap-2">
              <i class="fa-solid fa-phone-arrow-up-right text-lg"></i>
              <span>DIAL OUTBOUND EMERGENCY CALL</span>
            </button>
          </form>
        </div>

        <!-- Quick Presets -->
        <div class="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <p class="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">Quick Personnel Presets</p>
          <div class="flex flex-wrap gap-2">
            <button onclick="setPreset('+923172532350', 'Hamza (Safety Officer)', 'Downtown LA Freight Yard', 109.5)"
              class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-xs font-medium text-slate-300 transition flex items-center gap-1.5">
              <i class="fa-solid fa-user-check text-rose-400"></i> Hamza (+923172532350)
            </button>
            <button onclick="setPreset('+12135550192', 'Carlos Rodriguez (Civil Supervisor)', 'Port of Long Beach Terminal', 106.0)"
              class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-xs font-medium text-slate-300 transition flex items-center gap-1.5">
              <i class="fa-solid fa-hard-hat text-amber-400"></i> Carlos (+12135550192)
            </button>
            <button onclick="setPreset('+15595550199', 'Elena Morales (Central Valley Ag)', 'Fresno Solar & Ag Field', 111.0)"
              class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-xs font-medium text-slate-300 transition flex items-center gap-1.5">
              <i class="fa-solid fa-wheat-awn text-emerald-400"></i> Elena (+15595550199)
            </button>
          </div>
        </div>

      </div>

      <!-- Right Column: Live Call Stream & Telemetry (5 cols) -->
      <div class="lg:col-span-5 space-y-6">
        
        <div class="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col h-full">
          <div class="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
            <h3 class="text-sm font-bold text-white flex items-center gap-2">
              <i class="fa-solid fa-wave-square text-rose-400"></i> Live Call Stream & Telemetry
            </h3>
            <span id="callStatusBadge" class="text-xs px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700 font-mono font-bold">
              IDLE
            </span>
          </div>

          <!-- Status Card -->
          <div id="liveStreamBox" class="bg-slate-950 border border-slate-800 rounded-xl p-4 flex-1 space-y-3 font-mono text-xs text-slate-300">
            <div class="text-slate-500 flex items-center gap-2">
              <i class="fa-solid fa-circle-info"></i> No active call. Enter phone number and click Dial Outbound Call.
            </div>
          </div>

          <!-- Structured Result Box -->
          <div class="mt-4 pt-4 border-t border-slate-800">
            <p class="text-xs font-semibold text-slate-400 mb-2 flex items-center justify-between">
              <span>Structured Verification Result (`result_schema`)</span>
              <i class="fa-solid fa-code text-slate-500"></i>
            </p>
            <div id="resultBox" class="bg-slate-950/80 border border-slate-800 rounded-xl p-3 text-xs font-mono text-slate-400 overflow-x-auto">
              {"worker_acknowledged": null, "call_id": null}
            </div>
          </div>
        </div>

      </div>

    </div>
  </main>

  <script>
    const tempRange = document.getElementById('tempRange');
    const tempBadge = document.getElementById('tempBadge');
    tempRange.addEventListener('input', () => {
      tempBadge.textContent = tempRange.value + '°F';
    });

    function setPreset(phone, name, site, temp) {
      document.getElementById('phoneNumber').value = phone;
      document.getElementById('workerName').value = name;
      document.getElementById('siteName').value = site;
      tempRange.value = temp;
      tempBadge.textContent = temp + '°F';
    }

    let pollInterval = null;

    document.getElementById('dispatchForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = document.getElementById('btnTrigger');
      const streamBox = document.getElementById('liveStreamBox');
      const statusBadge = document.getElementById('callStatusBadge');
      const resultBox = document.getElementById('resultBox');

      const payload = {
        phone_number: document.getElementById('phoneNumber').value,
        worker_name: document.getElementById('workerName').value,
        site_name: document.getElementById('siteName').value,
        temperature_f: parseFloat(tempRange.value),
        work_rest_ratio: document.getElementById('workRestRatio').value,
        hydration_liters_per_hour: 1.5,
        cooling_refuge_direction: document.getElementById('coolingRefuge').value
      };

      btn.disabled = true;
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin text-lg"></i> <span>DIALING OUTBOUND VIA CALL-E...</span>';
      statusBadge.className = 'text-xs px-2.5 py-1 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono font-bold animate-pulse';
      statusBadge.textContent = 'DIALING';

      streamBox.innerHTML = `
        <div class="text-amber-400 flex items-center gap-2">
          <i class="fa-solid fa-spinner fa-spin"></i> Initializing conversational phone task...
        </div>
        <div class="text-slate-400">Target: ${payload.worker_name} (${payload.phone_number})</div>
        <div class="text-slate-400">Hazard: ${payload.temperature_f}°F at ${payload.site_name}</div>
      `;

      try {
        const resp = await fetch('/dispatch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!resp.ok) {
          const err = await resp.json();
          throw new Error(err.detail || 'Dispatch failed');
        }

        const data = await resp.json();
        const callId = data.call_id;

        statusBadge.className = 'text-xs px-2.5 py-1 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30 font-mono font-bold animate-pulse';
        statusBadge.textContent = 'RINGING / ACTIVE';

        streamBox.innerHTML += `
          <div class="text-emerald-400 font-bold">✅ Call Task Created!</div>
          <div class="text-slate-300">Call ID: <span class="text-rose-400 font-bold">${callId}</span></div>
          <div class="text-slate-400">Status: <span class="text-amber-300">${data.status.toUpperCase()}</span></div>
          <div class="text-slate-500 text-[11px] pt-2 border-t border-slate-800">Streaming live call events from CALL-E API...</div>
        `;

        if (pollInterval) clearInterval(pollInterval);
        
        let attempts = 0;
        pollInterval = setInterval(async () => {
          attempts++;
          try {
            const pollResp = await fetch('/call/' + callId);
            if (pollResp.ok) {
              const pollData = await pollResp.json();
              const st = pollData.status || (pollData.data && pollData.data.status) || 'in-progress';
              resultBox.textContent = JSON.stringify(pollData, null, 2);

              if (st === 'completed' || st === 'ended' || attempts > 20) {
                clearInterval(pollInterval);
                statusBadge.className = 'text-xs px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono font-bold';
                statusBadge.textContent = 'COMPLETED';
                streamBox.innerHTML += `<div class="text-emerald-400 font-bold pt-2">🎯 Call Session Finished! Structured Result Extracted.</div>`;
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-phone-arrow-up-right text-lg"></i> <span>DIAL OUTBOUND EMERGENCY CALL</span>';
              }
            }
          } catch (e) {
            console.error('Polling error:', e);
          }
        }, 3000);

      } catch (err) {
        statusBadge.className = 'text-xs px-2.5 py-1 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30 font-mono font-bold';
        statusBadge.textContent = 'ERROR';
        streamBox.innerHTML += `<div class="text-rose-400 font-bold">❌ Error: ${err.message}</div>`;
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-phone-arrow-up-right text-lg"></i> <span>DIAL OUTBOUND EMERGENCY CALL</span>';
      }
    });
  </script>
</body>
</html>
"""


@app.get("/health")
def health():
    return {"status": "ok", "calle_base_url": settings.calle_base_url}


@app.post("/dispatch", response_model=CallDispatchResult)
async def dispatch_call(payload: HeatSafetyPayload):
    """Trigger an autonomous outbound emergency phone call to field personnel."""
    try:
        result = await trigger_heat_call(
            payload=payload,
            api_key=settings.calle_api_key,
            base_url=settings.calle_base_url,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/call/{call_id}")
async def get_call_status(call_id: str):
    """Fetch call status and structured worker acknowledgment from CALL-E."""
    try:
        data = await poll_call_status(
            call_id=call_id,
            api_key=settings.calle_api_key,
            base_url=settings.calle_base_url,
            max_wait_seconds=5,
        )
        return data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=settings.host, port=settings.port, reload=True)
