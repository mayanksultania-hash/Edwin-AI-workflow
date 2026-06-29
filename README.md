# AI Workflow

Turn a plain-English request into a runnable workflow.

## Simple guide

Describe what you want in normal language. The system figures out the steps, builds
a workflow, generates code, and runs it in **practice mode** (mock tools — no real
ServiceNow, Okta, or alerts yet).

```text
You type a request
  -> system understands what you want
  -> system plans the steps
  -> system generates the workflow and code
  -> system verifies the generated code
  -> system runs the workflow
  -> you get a result
```

**Try it (CLI):**

```bash
.venv/bin/ai-workflow "When a critical router event happens, create an alert and ServiceNow incident" --config config/workflow_config.yaml
```

Need real AI? Set `OPENAI_API_KEY` in `.env`. Default config already uses
`model.provider: openai`. For offline try-it runs, set `model.provider: mock` in
`config/workflow_config.yaml`.

## Sample user inputs

Copy one of these into the CLI or Streamlit text box.

### Example 1: Incident workflow

**User input:**

```text
When a critical router event happens, create an alert and ServiceNow incident
```

**What happens:**

```text
1. Match the critical router event
2. Create an alert
3. Create a ServiceNow incident
```

### Example 2: Access request

**User input:**

```text
Give John Tableau access
```

**What happens:**

```text
1. Request access for John to Tableau
2. Grant the access
```

If required details are missing (for example `Give Tableau access` with no user),
the system stops and asks for the missing information.

---

## Prerequisites

- Python 3.12+
- Node.js (only if using the default TypeScript output)
- OpenAI API key (or set `model.provider: mock` in config for offline runs)

## Quick start

```bash
git clone <repo-url>
cd Edwin-AI-workflow

python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install --no-deps -e .
cp .env.example .env   # then set OPENAI_API_KEY=your-key
```

## Config

File: `config/workflow_config.yaml`

Default config uses **OpenAI**. For a no-API-key try-it run, set
`model.provider: mock` instead of `openai`.

```yaml
model:
  provider: openai          # or mock for offline runs
  name: gpt-4.1-mini
  api_key_env_var: OPENAI_API_KEY
  max_output_tokens: 1200

generation:
  output_language: typescript   # or python

tools:
  enabled:
    - event_tool
    - alert_tool
    - servicenow_tool
    - access_tool
```

- **mock** provider — no API key, fixed responses for tests
- **openai** provider — real intent, plan, and workflow YAML from the LLM
- **typescript** — generates `.ts` and runs via Node when available
- **python** — generates `.py` and runs via the Python code runner

## Troubleshooting

- `Missing API key env value: OPENAI_API_KEY` — create `.env` from `.env.example`
  or switch config to `model.provider: mock`
- TypeScript run issues — install Node.js or switch config to `output_language: python`
- Command not found — run from the repo root after creating `.venv` there

## Run CLI

```bash
# Example 1: incident workflow
.venv/bin/ai-workflow "When a critical router event happens, create an alert and ServiceNow incident" --config config/workflow_config.yaml

# Example 2: access request
.venv/bin/ai-workflow "Give John Tableau access" --config config/workflow_config.yaml

# Save full run details to a checkpoint JSON file
.venv/bin/ai-workflow "Give John Tableau access" --config config/workflow_config.yaml --checkpoint-dir outputs/test_run_output

# Validate saved YAML without calling the LLM
.venv/bin/ai-workflow --validate-yaml examples/access_request.workflow.yaml --config config/workflow_config.yaml
```

CLI output includes: intent, plan, workflow YAML, generated code, code verification,
execution result, and file paths.

## Run Streamlit

```bash
.venv/bin/ai-workflow-ui
```

If the script is not installed yet, use:

```bash
.venv/bin/python -m streamlit run src/ai_workflow/ui/streamlit_app.py
```

For a simple demo:

1. Select `Action Group`.
2. Use this request:

```text
Create an Incident Processing action group for ServiceNow incident updates
```

3. Click `Generate action group`.
4. Show these tabs:
   - `General`
   - `Actions`
   - `Action Group YAML`
   - `Action Service JSON`
   - `Submit Result`

Keep `Approve and submit Action Service JSON` unchecked for demo mode. The default
config is preview-only and does not call Action Service.

## Run tests

```bash
.venv/bin/python -m pytest tests
```

---

## How it works (for developers)

```text
prompt
  -> AI intent detection
  -> context check (missing required inputs stop early)
  -> AI plan + workflow YAML
  -> validation (tools, step references)
  -> template-based code generation (Python or TypeScript)
  -> AI semantic code verification
  -> execute generated code (mock tools)
  -> audit + saved files
```

**AI generates:** intent, plan, workflow YAML.

**AI verifies:** generated code matches the request and workflow YAML.

**Templates generate:** final Python/TypeScript code from YAML.

**Runtime values** use `$context.field` (for example `$context.user`).
**Step outputs** use `$steps.step_id.field`.

Sample workflow YAML files: `examples/`

## Mock tools

These simulate external systems — nothing calls real APIs yet.

```text
event_tool.match_event
alert_tool.create_or_update_alert
servicenow_tool.create_incident
access_tool.request_access
access_tool.grant_access
```

## Project layout

```text
src/ai_workflow/
  app.py, main.py          entrypoints
  orchestration/           intent, plan (LLM + templates)
  generator/               YAML -> code templates
  engine/                  validation, runners, audit
  integrations/            Python integration wrappers
  tools/                   mock tool registry
  ui/                      Streamlit app
config/workflow_config.yaml
examples/
outputs/audit/             run audit JSON
outputs/generated/         workflow YAML + generated code
outputs/test_run_output/   detailed checkpoint JSON per run
```

## Next steps

```text
1. Real MCP context instead of mock gatherer
2. Real ServiceNow, Okta, alert, and event integrations
3. Follow-up chat flow to collect missing context in one session
4. Approval guardrails before real external actions
```
