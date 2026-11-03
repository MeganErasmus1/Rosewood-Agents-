# OneDrive Setup

Set this up once. The automation depends on these exact names.

```
/Rosewood/
├── Clients/
│   └── {Client Name}/
│       └── {Policy No} {Product}/          e.g. "ETU000999 CAR"
│           ├── Schedules/                  every schedule received, prefixed with the date
│           ├── Wording/
│           ├── Records/                    policy records (agent Part A + broker Part B)
│           └── Correspondence/
├── Agent/
│   ├── Incoming/                           temporary: PDFs land here before filing
│   ├── Wordings Library/                   one PDF per insurer wording, plus the key-points .md files
│   ├── Client List.xlsx                    table name: Clients
│   ├── Renewal Register.xlsx               table name: Register
│   └── Corrections Log.xlsx                admin logs every change she makes to an agent draft
└── Compliance/
    └── Operators/                          POPIA operator agreements
```

## Excel files
Each file needs its data formatted as an **Excel Table** (Insert > Table), with the table name shown above. Make can only read and write named tables.

- **Renewal Register:** columns from `templates/renewal-register.csv`.
- **Client List:** columns from `templates/client-list.csv`. This is how the agent knows who to address the email to. Insurer schedules often leave out the client's contact details (Excelsus and Kopanetse both do).
- **Corrections Log:** `date, policy_number, section, what_agent_wrote, what_it_should_be, type (figure / wording / tone / missed flag)`.

## Matching rule
**Policy number is the key, not client name.** Names vary between schedules ("Excelsus Build" vs "Excelsus Build (Pty) Ltd"). The flow looks up the policy number in the Client List first. If the policy is new, it falls back to the client name. If it finds no match, it creates the draft with an empty "To" field and asks the admin to add the client to the list.

## One-off task
Load your existing clients into the Client List, with policy number, contact name, email and folder name. Your admin can do this in about an hour. Without it, every draft needs the recipient added by hand.
