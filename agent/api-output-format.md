# API Output Format (automated mode)

Add this to the end of the system prompt when the agent runs through the automation. The flow needs the response as machine-readable JSON.

---

## Output format

Return **only** a single valid JSON object, with no text before or after it. Use this structure:

```json
{
  "status": "READY_TO_SEND | SEND_AFTER_QUERIES_LOGGED | HOLD_ESCALATE",
  "document_type": "schedule | wording | endorsement | other",
  "transaction_type": "new_business | renewal | endorsement | unknown",
  "client_name": "",
  "policy_number": "",
  "product": "",
  "flags": [
    { "level": "RED | AMBER | GREEN", "issue": "", "source": "" }
  ],
  "email": {
    "subject": "",
    "body_html": ""
  },
  "broker_check_html": "",
  "policy_record_html": "",
  "register_row": {
    "client_name": "", "policy_number": "", "product": "", "insurer": "",
    "underwriting_manager": "", "policy_type": "", "inception_date": "YYYY-MM-DD",
    "expiry_date": "YYYY-MM-DD", "renewal_date": "YYYY-MM-DD",
    "renewal_action_date": "YYYY-MM-DD", "annual_premium": "", "monthly_premium": "",
    "payment_frequency": "", "max_contract_value": "", "contract_end_date": "",
    "maintenance_period": "", "status": "", "open_flags": "", "notes": ""
  }
}
```

## Rules
- `renewal_action_date` = `renewal_date` minus 60 days. This is the only calculation you may do.
- `body_html`: simple HTML that pastes cleanly into Outlook. Use `<p>`, `<b>`, `<ul>`, `<ol>` and `<table>` with inline borders only. No CSS classes, no images.
- If the attachments contain no policy schedule (only a wording, a debit order form or similar), set `document_type` accordingly, set `status` to `HOLD_ESCALATE`, and explain in `broker_check_html`. Do not invent a summary.
- If `status` is `HOLD_ESCALATE`, still write the email so the broker can edit it once the issues are resolved.
- Dates you can't find in the document: use an empty string, never a guess.
