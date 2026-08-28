---
name: heat-safety-dispatcher
description: Autonomous emergency voice dispatcher for outdoor workforce heat safety powered by CALL-E Voice AI. Dispatches outbound conversational phone calls to workers and supervisors when extreme temperature or WBGT heat strain is detected.
version: 1.0.0
author: Hamza Naseem
tags:
  - phone-call
  - voice-agent
  - emergency-dispatch
  - worker-safety
  - occupational-health
  - osha
---

# Heat Safety Emergency Voice Dispatcher (CALL-E Skill)

An autonomous, closed-loop voice agent skill that turns environmental heat alerts and thermal strain thresholds into real, conversational phone calls to outdoor workers, construction foremen, and agricultural supervisors.

## Why This Skill Exists
Standard digital alerts (SMS, push notifications, email) are frequently missed by outdoor personnel actively operating heavy machinery, wearing protective equipment, or working in direct sunlight. This skill equips any autonomous AI agent (ChatGPT, Claude Code, Codex, LangChain, MCP) with the ability to **dial the worker's phone directly**, convey urgent OSHA-mandated work/rest cycles and hydration quotas, and return a **structured acknowledgment record**.

## When to Trigger
Invoke this skill whenever:
1. Microclimate or ambient temperature crosses extreme safety thresholds ($\ge 105^\circ\text{F}$ or elevated heat index).
2. ISO 7243 / OSHA Wet Bulb Globe Temperature (WBGT) indicates high heat-stroke risk.
3. An emergency heat-break or immediate site evacuation must be communicated directly to field personnel.

## Parameters
| Parameter | Type | Required | Description | Example |
| :--- | :--- | :---: | :--- | :--- |
| `phone_number` | string | Yes | Worker or supervisor E.164 phone number | `"+12135550192"` |
| `worker_name` | string | Yes | Name of the worker or team lead | `"Carlos Rodriguez"` |
| `site_name` | string | Yes | Work site or facility location | `"Downtown LA Logistics Hub"` |
| `temperature_f` | float | Yes | Current surface/ambient temperature | `108.5` |
| `work_rest_ratio` | string | No | Mandated OSHA work/rest schedule | `"15 min work / 45 min rest"` |
| `hydration_liters_per_hour` | float | No | Mandated water consumption quota | `1.5` |
| `cooling_refuge_direction` | string | No | Compass bearing/direction to shaded relief | `"North-East (Sector B)"` |

## Output Schema
The skill polls CALL-E and returns a structured JSON payload:
```json
{
  "call_id": "call_zDKso-_P7z9D8s-Bc-GxDQ",
  "status": "completed",
  "worker_acknowledged": true,
  "summary": "Worker Carlos acknowledged the 108.5°F extreme heat advisory, confirmed taking a 45-minute shade break, and drank 1.5L of water.",
  "duration_seconds": 48,
  "timestamp": "2026-08-29T02:20:00Z"
}
```
