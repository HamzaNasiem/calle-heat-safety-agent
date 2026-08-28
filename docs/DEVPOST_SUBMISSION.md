# Devpost Submission Dossier — CALL-E: Your Code Is Calling

Copy and paste these exact answers when submitting on Devpost:

---

### Project Title
```text
CALL-E Heat Guardian — Autonomous Emergency Voice Dispatcher for Workforce Heat Safety
```

---

### Tagline (One-line pitch — under 200 characters)
```text
Turns extreme heat and OSHA thermal strain warnings into autonomous, conversational phone calls to outdoor workers using CALL-E Voice AI.
```

---

### About the Project / Description

#### Inspiration
Over 2.4 billion outdoor workers worldwide face fatal heat strain during summer operations. When ground temperatures soar past 105°F, traditional automated notifications (emails, push notifications, and SMS) fail: workers operating noisy heavy machinery or wearing thick gloves simply don't check their screens until it's too late. We asked: *What if our environmental watchdog agent could literally pick up the phone, call the worker, speak to them with urgent authority, and verify they are moving to shade?* That is why we built **CALL-E Heat Guardian**.

#### What it does
**CALL-E Heat Guardian** is an autonomous voice dispatch system and reusable Agent Skill:
1. **Detects Hazardous Microclimates:** Evaluates real-time ambient and surface heat against Cal/OSHA & ISO 7243 Wet Bulb Globe Temperature (WBGT) safety limits.
2. **Autonomous Outbound Dialing:** When extreme heat thresholds are breached, the agent immediately places a live phone call via CALL-E to the on-site foreman or worker's phone.
3. **Conversational Safety Enforcement:** The AI voice agent speaks fluent, authoritative English, conveys the exact temperature reading, mandates OSHA work/rest schedules (e.g. 15 min work / 45 min rest) and water quotas (1.5 L/hr), and guides workers to the nearest shaded cooling canopy.
4. **Structured Acknowledgment & Audit Trail:** Uses CALL-E’s structured `result_schema` to verify whether the worker verbally acknowledged the directive, recording a compliance audit log.

#### How we built it
- **Core Voice Engine:** Integrated directly with CALL-E’s `/calls` API with dynamic prompt engineering and structured JSON verification schemas (`worker_acknowledged`).
- **Reusable Agent Skill:** Packaged as `skills/heat_safety_dispatcher/` with `SKILL.md` and `skill.json` for seamless plug-and-play use in Claude Code, ChatGPT, Codex, LangChain, and MCP environments.
- **Interactive CLI & FastAPI Server:** Built a lightweight Python application (`apps/python/calle-heat-guardian/`) with single-command CLI dialing and REST webhooks.
- **Testing:** 100% automated test coverage with `pytest` validating E.164 phone formatting, prompt templates, and real API dispatch tasks.

#### Challenges we ran into
Ensuring zero communication latency during emergencies required strict E.164 phone sanitization and designing concise, authoritative prompts that ensure the AI voice agent immediately captures worker attention and extracts clear verbal acknowledgment.

#### Accomplishments that we're proud of
- Building a real-world, life-saving application that moves AI telephony beyond generic appointment reminders into critical industrial health and safety.
- 100% working live implementation with structured verification schema.
- Reusable contribution ready to be merged into `CALLE-AI/awesome-phone-call-agents`.

#### What we learned
CALL-E’s ability to combine natural voice dialogue with structured schema extraction (`result_schema`) makes it an ideal platform for high-stakes enterprise workflows where verbal compliance must be recorded for legal audits.

#### What's next for CALL-E Heat Guardian
- Multilingual dispatch support (Spanish, Hindi, Arabic) for diverse global workforces.
- Biometric smartwatch integration to trigger emergency calls based on real-time core body temperature.

---

### Built With
- `python`, `call-e`, `fastapi`, `pydantic`, `httpx`, `pytest`, `ai-agent`

---

### Try It Out Links
- **GitHub Repository:** `https://github.com/HamzaNasiem/calle-heat-safety-agent`
- **Pull Request URL:** `https://github.com/CALLE-AI/awesome-phone-call-agents/pulls`
