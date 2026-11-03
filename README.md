# Rosewood Agents

AI agents for Rosewood Insurance Brokers.

## 1. Policy Summary Agent

Reads every new or renewed policy schedule and produces:

- a plain-English **client email** summarising cover, deductibles, exclusions and the conditions the client must meet
- an internal **broker check** with red, amber and green flags (for example, a contract that falls inside the policy's own exclusions)
- a **policy record** for the client file, with a FAIS advice section left for the broker to complete
- a **renewal register** row, so every policy is tracked from the day it lands

A human approves everything before it goes out.

| Folder | Contents |
|---|---|
| `agent/system-prompt.md` | The agent's instructions |
| `templates/` | Client email, policy record, renewal register |
| `knowledge/wordings/` | Key points per insurer wording |
| `docs/automation-plan.md` | Phase 1 (Claude Project), Phase 2 (Outlook + Power Automate), Phase 3 (renewals) |

**Products live:** Contractors All Risk (Elevation / Bryte).
**Next:** performance guarantees, liability, EVsure. Each gets its own template and wording notes as policies come in.

**Client data:** client schedules and generated summaries are not stored in this repo (POPIA). They belong in the client folders.
