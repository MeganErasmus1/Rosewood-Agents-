# Policy Summary Agent: Scheduled Run Runbook

This is what every scheduled run does. It uses the Microsoft 365 connector (MDM account, Megan@mdmrisks.com). **Do not send any email. Do not edit, move, rename or delete any existing client file.** The only writes allowed are: Outlook **drafts**, new summary `.docx` files, and files inside the agent's own state folder.

## Fixed locations (OneDrive, MDM)

| What | Value |
|---|---|
| driveId | `b!7vzr3uRy1k65KuSVa9BOZFDXW55shcdHi9qqW2LLvkPSVZnnH9wsTJm5WOe1Oaaa` |
| Client database root | `4. ROSEWOOD INSURANCE BROKERS (PTY) LTD/CLIENT DATABASE` (item `01CO7KXES5JTQ45J5ZNJHKAFOW3F3MKJY5`) |
| Agent state folder | `CLIENT DATABASE/_policy-summary-agent/` (item `01CO7KXESSBZVZ4D72JJFLKYXIN4GKGAEF`, contains `processed.json`) |
| Client list (read only) | `CLIENT DATABASE/CLIENT DATABASE ORGANISED.xlsx` |
| Renewals agent (do not touch) | `CLIENT DATABASE/_renewals-agent/` |

Client folder pattern: `CLIENT DATABASE/CAR CLIENTS/{CLIENT}/{YEAR or POLICY}/` with schedules named like `{Client} ETU000999-CAR 28-10-2026.pdf`.

## Steps

1. **Set up.** Use `git checkout claude/policy-summary-agent-brld6y` if you're not already on it. Read `agent/system-prompt.md`, `templates/car-client-email.md`, `templates/policy-record.md` and `knowledge/wordings/*.md`. Get today's date in Africa/Johannesburg.

2. **Load state.** Read `_policy-summary-agent/processed.json`. It's a list of `{ "itemId", "name", "processed_on", "status", "draft_id" }`. If the file is missing, treat it as empty.

3. **Find new schedules.** Run `sharepoint_search` with query `ETU OR CAR OR schedule`, `fileType: pdf`, `folderName: CLIENT DATABASE` and `afterDateTime` = 10 days ago, and page through every result. Keep a file only if **all** of these are true:
   - its path is under `CLIENT DATABASE/` but not under `CLIENT DATABASE - Copy/`, `_renewals-agent/`, `_policy-summary-agent/`, `QUOTE`, `QUOTES` or `LEADS`
   - its name looks like a policy schedule: it contains a policy number pattern (`ETU\d{6}`, `CAR\d{7}`, `ACE ENG\d+`) or the word "schedule"
   - its name doesn't contain "wording", "SASRIA", "coupon", "debit order", "invoice", "quote" or "proposal"
   - its itemId isn't already in `processed.json`

   **On the first run, only process files modified in the last 10 days.** Never back-process the whole archive.

4. **For each new schedule** (maximum 5 per run, oldest first):
   - a. Read the PDF with `read_resource` (all pages).
   - b. Find the matching wording. Look in the same folder for a file with "wording" or the insurer's name in it, then fall back to `knowledge/wordings/`. If neither exists, say "wording not reviewed" in the broker check.
   - c. Look up the client's row in `CLIENT DATABASE ORGANISED.xlsx` by policy number, and check it for conflicts with the schedule (status, dates, insurer).
   - d. List the sibling folders of the client folder, such as `THEFT CLAIM`. An open claim folder must appear as a flag in the broker check, because it's relevant to warranties.
   - e. Follow `agent/system-prompt.md` exactly to produce the **broker check**, the **client email** and **Part A of the policy record**. Today's date is from step 1.
   - f. **Build the summary document.** Write the policy record (broker check + Part A + client email as sent + blank Part B) to a local `.md` file. Run `python3 agent/md_to_docx.py in.md out.docx`, then upload it with `sharepoint_upload_file` (contentBase64, `expectedBytes` = the printed size) into the **same folder as the schedule**. Name it `POLICY SUMMARY - {policy no} - {YYYY-MM-DD}.docx` and use `conflictBehavior: rename`.
     The base64 must be copied exactly. If the upload is refused for a size mismatch, rebuild and retry once, then fall back to uploading the same content as `.html` (from `agent/md_to_html.py`) via `content`.
   - g. **Create one Outlook draft** (`outlook_create_draft`, bodyType html, no recipients). Build the body with `python3 agent/md_to_html.py draft.md`, which outputs only tags the Outlook allowlist accepts. End every draft with: "Policy summary saved to the client folder in OneDrive. Add this policy to CLIENT DATABASE ORGANISED.xlsx if it is not there yet."
     - If the status is READY or SEND AFTER QUERIES:
       - Subject: `[READY] {Client} {Policy no}: copy to Rosewood mail` or `[QUERIES] ...`
       - Body: a short broker-check box at the top, a line `===== COPY FROM HERE INTO ROSEWOOD EMAIL =====`, then the client email.
     - If the status is HOLD:
       - Subject: `[HOLD] {Client} {Policy no}: escalate to Megan`
       - Body: the broker check only, with no client email.
   - h. Append the entry to `processed.json`.

5. **Save state.** Upload `processed.json` with `conflictBehavior: replace`. This is the only file the agent may ever replace.

6. **Report.**
   - If anything was processed, finish with a short summary: client, policy, status and the key flag, one line each.
   - If nothing new was found, finish with "No new schedules" and do nothing else.
   - **Never send email, never contact clients or insurers.**

## Rules
- Follow every accuracy rule in `agent/system-prompt.md`, especially the rule against invented figures.
- Never include commission or brokerage figures in the client email.
- South African English, no em-dashes.
- If anything fails partway, still save `processed.json` for the files completed, and report the failure plainly.
