# How the Agent Runs

## Phase 1: Claude Project (live now, zero build)

1. Create a Claude Project called **Rosewood Policy Summaries**.
2. Paste `agent/system-prompt.md` into the project instructions.
3. Upload these files to project knowledge: both templates, `renewal-register.csv`, and every file in `knowledge/wordings/` plus the full wording PDFs.
4. Admin workflow, per policy:
   - Open a new chat in the project. Drop in the schedule PDF (and the wording if it's new). Type: `New policy. Today is {date}.`
   - Read the **broker check** first. If it says `HOLD: ESCALATE TO MEGAN`, stop and forward it to Megan.
   - Otherwise check every figure in the email against the schedule (about 5 minutes), then paste the email into Outlook, attach the schedule and wording, and send.
   - Save the policy record as a PDF to the client folder.
   - Paste the register row into the renewal register.
5. Run this way for 4 to 6 weeks (about 20 to 30 policies). Log every correction the admin makes. That log is how we tune the prompt.

**Time per policy:** about 10 minutes, down from 45 to 60 to do it by hand.

## Phase 2: Automated intake (Microsoft 365)

Built in **Power Automate**, which is included in most Microsoft 365 Business plans. No server, no developer.

```
Insurer email lands in Outlook (from @elevationtu.co.za or another insurer domain, with a PDF attached)
  -> Power Automate saves the PDFs to OneDrive: /Clients/{Client}/Policies/{Policy No}/
  -> Sends the PDF and the system prompt to the Claude API
  -> Claude returns: email, broker check, record, register row
  -> Power Automate:
       - creates a DRAFT reply in Outlook (never sends)
       - saves the policy record to the client folder
       - adds a row to the Renewal Register (Excel in OneDrive)
       - emails the broker check to the admin, flagged RED/AMBER/GREEN
  -> Admin reviews the draft, edits if needed, clicks send
```

**Rough cost:** Claude API about R5 to R15 per policy at current volumes. Power Automate premium connector (HTTP) about R280/month per user, only if the plan doesn't already include it.

## Phase 3: Renewal engine (uses the register)

- A daily flow reads the register. At `renewal_action_date` (60 days before renewal) it emails the admin a renewal task with the client's current cover summary.
- At 30 days it drafts a client email asking for contract updates (new contracts, turnover, values).
- When the renewal schedule arrives, the agent compares it against last year's record and flags every change in cover, deductibles or premium.

## Open decisions
- Where client folders live today (OneDrive, SharePoint, local drive or Dropbox).
- Whether the M365 plan includes Power Automate premium connectors.
- POPIA: add a line to the client mandate or privacy notice covering AI-assisted processing.
