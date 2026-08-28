# Pull Request: Add Heat Safety Emergency Voice Dispatcher to Agent Skills & Apps

**Target Repository:** [`CALLE-AI/awesome-phone-call-agents`](https://github.com/CALLE-AI/awesome-phone-call-agents)  
**Contribution Area:** `skills/` and `apps/python/`  
**Author:** Hamza Naseem  

---

### 📝 Description of Contribution
This pull request adds **Heat Safety Emergency Voice Dispatcher** (`skills/heat_safety_dispatcher/` and `apps/python/calle-heat-guardian/`) to the CALL-E ecosystem.

It demonstrates a high-impact, life-saving application of CALL-E: converting dangerous physical environmental temperature and OSHA thermal strain warnings into autonomous outbound phone calls to outdoor workers, construction foremen, and agricultural crews.

### 🌟 Key Highlights:
1. **Reusable Agent Skill (`skills/heat_safety_dispatcher/`):**
   - Includes `SKILL.md` and `skill.json` compatible with Codex, ChatGPT, Claude Code, LangChain, and MCP environments.
   - Accepts structured heat parameters (temperature, worker name, site name, OSHA work/rest ratio, hydration quota, and shaded refuge direction).
2. **Structured Verification Schema:**
   - Enforces CALL-E's structured `result_schema` returning `worker_acknowledged` boolean upon spoken confirmation by the field worker.
3. **Runnable Python App & CLI (`apps/python/calle-heat-guardian/`):**
   - Single-command CLI dialer (`main.py`) and FastAPI REST service (`server.py`).
4. **100% Passing Unit Test Suite:**
   - Full test coverage in `tests/test_calle_integration.py` verifying E.164 sanitization, prompt construction, and live API dispatch.

### 🧪 Verification Checklist:
- [x] Skill follows repository naming conventions and structure.
- [x] Includes `SKILL.md` with parameters and return schema.
- [x] Tested with real CALL-E phone calls.
- [x] Zero external heavy dependencies.
