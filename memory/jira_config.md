# Jira Project Config — KNOW (Customer Education)

Use this file when filing new issues or automating Jira workflows via the Atlassian MCP.

## Core Fields

| Field | Value |
|---|---|
| Cloud ID | `646a4867-d35f-4b64-958d-eb9a1def6740` |
| Project key | `KNOW` |
| Project ID | `10020` |
| Issue type | Task (`10002`) |
| Assignee account ID | `5a6103bb9d0ea46a7a5b6cde` (sam.walker@safe.com) |
| Component | Development (`id: 15340`) |
| Class of Service | `customfield_10253`: `{"value": "Standard"}` |

## Creating an Issue

```
createJiraIssue(
  cloudId      = "646a4867-d35f-4b64-958d-eb9a1def6740"
  projectKey   = "KNOW"
  issueTypeName = "Task"
  summary      = "..."
  description  = "..."   # markdown
  contentFormat = "markdown"
  assignee_account_id = "5a6103bb9d0ea46a7a5b6cde"
  additional_fields = {
    "components": [{"name": "Development"}],
    "customfield_10253": {"value": "Standard"}
  }
)
```

## Workflow Transition IDs

New issues start in **In Backlog** (status category: To Do).

| Transition | ID | From state | To state |
|---|---|---|---|
| Ready for Work | `241` | In Backlog | Ready for Work |
| Begin Work | `211` | Ready for Work | In Progress |
| Work Complete | `31` | In Progress | Ready for QA |
| Closed Complete | `301` | In Progress | Closed (Done) |
| Won't Do | `201` | In Backlog / Ready for Work | Closed |

### Path to Done (fixed/completed issues)
`create` → `241` → `211` → `301`

### Path to Ready for QA (implemented, awaiting review)
`create` → `241` → `211` → `31`

### Won't Do
`create` → `201`

## Board URL
https://safesoftware.atlassian.net/jira/software/projects/KNOW/boards
