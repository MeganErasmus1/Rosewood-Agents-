# How the Agent Runs

## Phase 1: Claude Project (start here, works today)

1. Create a Claude Project called **Rosewood Policy Summaries**.
2. Paste `agent/system-prompt.md` into the project instructions.
3. Upload to project knowledge: the templates, `knowledge/wordings/*`, and the full wording PDFs.
4. **Admin, per policy:** drop the schedule PDF into a new chat and type `New policy. Today is {date}.` Then:
   - Read the broker check first. If it says HOLD, forward it to Megan.
   - Check the email figures against the schedule, paste the email into Outlook, attach the PDFs, and send.
   - Save the record to the client folder and add the row to the register.
   - Log every correction in `Corrections Log.xlsx`.

Run Phase 1 in parallel while Phase 2 is being built. The corrections log is what makes Phase 2 accurate.

---

## Phase 2: Automated intake (Outlook + OneDrive + Make + Claude API)

### Why Make, not Power Automate
Microsoft 365 Business includes Power Automate, but calling an external AI service needs its **HTTP connector, which is Premium** and charged per user per month. Make's HTTP module is available on every plan. It connects natively to Outlook, OneDrive and Excel, and it's easier to fix without a developer. If your plan already includes Power Automate Premium, the same design works there.

### What you need
| Item | Where | Notes |
|---|---|---|
| Anthropic API account | console.anthropic.com | Separate from your Claude subscription. Add a card and set a **monthly spend limit** (start at USD 20). Create an API key. |
| Make account | make.com | The Core plan is enough at this volume. |
| OneDrive structure | `docs/onedrive-setup.md` | Folders plus 3 Excel tables. |
| Outlook rule | Outlook | Moves insurer emails into a folder called `Insurer Schedules`. |

### Step 1: Outlook rule (free, 5 minutes)
Set up a rule: **From** contains `elevationtu.co.za` (add other insurer domains as you go) **and** has an attachment, then **copy** to the folder `Insurer Schedules`. Copy rather than move, so the original stays in your inbox.

### Step 2: Make scenario "Policy Intake"
| # | Module | Setting |
|---|---|---|
| 1 | Microsoft 365 Email: **Watch Emails** | Folder `Insurer Schedules`, every 15 min |
| 2 | Microsoft 365 Email: **Iterate Attachments** | Filter: filename ends in `.pdf` |
| 3 | OneDrive: **Upload a File** | `/Rosewood/Agent/Incoming/{{date}}/{{filename}}` |
| 4 | Tools: **Array Aggregator** | Builds one Claude "document" block per PDF (`type: document`, `source: base64`, `media_type: application/pdf`) |
| 5 | HTTP: **Make a Request** | POST `https://api.anthropic.com/v1/messages`. Headers: `x-api-key`, `anthropic-version: 2023-06-01`, `content-type: application/json`. Body: `model`, `max_tokens: 16000`, `system` = system prompt + wording key points + `agent/api-output-format.md`, and `messages` = the PDF blocks + `"Today is {{formatDate(now)}}. Email subject: {{subject}}."` |
| 6 | JSON: **Parse JSON** | Parses `content[0].text` against the structure in `api-output-format.md` |
| 7 | Excel: **Search Rows** | Client List: `policy_numbers` contains `{{policy_number}}`, else `client_name` |
| 8 | OneDrive: **Create Folder** (if missing) and **Move** the PDFs | `/Rosewood/Clients/{{folder_name}}/{{policy_number}} {{product}}/Schedules/` |
| 9 | OneDrive: **Upload a File** | Policy record as `{{date}} {{policy_number}} Policy Record.html` in `Records/`. It opens in Word, where the broker completes Part B and saves it as PDF. |
| 10 | Excel: **Search Rows** in Register, by policy number | Found: **Update Row**. Not found: **Add Row**. |
| 11 | Router: **status ≠ HOLD_ESCALATE** | Microsoft 365 Email: **Create a Draft**. To: client email (blank if not found). Subject and body from the agent. Attach the PDFs. **Never "Send".** |
| 12 | Router: **always** | Email the admin the broker check, with the subject `[{{status}}] {{client_name}} {{policy_number}}`. If status is HOLD, CC Megan. |
| 13 | Router: **ai_opt_out = Yes** | Skip modules 5 to 11 and email the admin: "Client opted out of AI processing, summarise by hand". |

**Model:** use the current most capable Claude model listed in Anthropic's docs. Accuracy on figures matters more than the small cost difference at this volume.

**Error handling:** add an error route on module 5 that emails the admin "Agent failed on {{subject}}, process by hand". A failed run must never be silent.

### Step 3: Make scenario "Renewal Reminders" (daily, 07:00)
1. Excel Search Rows in Register where `renewal_action_date` = today, then email the admin: renewal task, current cover, open flags.
2. Where `renewal_date` is 30 days from today, draft a client email asking for an updated contract list, turnover and claims since inception.
3. Where `expiry_date` is in the past and `status` = Active, email Megan. This catches the Kopanetse situation.

### Step 4: Test before go-live
Run the 3 sample PDFs (Excelsus, Kopanetse, the wording on its own) through the scenario and check:
- Kopanetse comes back as `HOLD_ESCALATE` and creates no client draft.
- Excelsus creates a draft with figures that match the schedule line by line.
- A wording-only email comes back as HOLD with `document_type: wording`.

### Running cost (estimate, check after the first month)
- **Make Core:** roughly USD 10 to 11 per month.
- **Claude API:** a 12 to 15 page schedule costs cents to well under a dollar per policy, depending on the model. The Anthropic console shows the exact cost of each call, so check it after the first 3 runs. The spend limit protects you either way.

### Build effort
About one afternoon for someone comfortable with Make, or 2 to 3 hours of a freelancer's time. The Outlook rule, OneDrive folders and Excel tables can be set up by your admin.

---

## Phase 3: Renewal comparison
When a renewal schedule arrives for a policy already in the register, the agent also receives last year's record and flags every change in limits, deductibles, conditions and premium. Build this after 2 to 3 months of Phase 2 data.
