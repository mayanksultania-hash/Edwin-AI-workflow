# LM Alert Processing — guided setup

This package customizes the **LM Alert Processing** action group through a short Q&A flow: the LLM asks questions, you answer in plain English, and Python applies safe patches to produce a final YAML file.

**Base workflow (input):** `inputs/lm_alert_processing_base.yaml`  
**Output:** `outputs/generated/lm_alert_processing/final.yaml`  
**UI:** Streamlit mode **“LM Alert guided setup”**

---

## Folder structure (simple map)

```text
lm_alert_processing/
├── customizer.py          # Main entry: questions → patches → final YAML
├── config/                # Static rules and catalogs (edit YAML here)
│   ├── constants.py       # IDs, paths, allowed patch types / fields
│   ├── action_ids/        # Reusable Action ID layer (platform building blocks)
│   └── action_group/      # This workflow’s step groups (guided questions)
├── prompts/               # Jinja templates sent to the LLM
├── core/                  # Patch apply, validation, LLM JSON models
└── helpers/               # I/O, prompt assembly, small utilities
```

---

## Two config layers (read this first)

Think of the base YAML as the full recipe. These two folders are **short cheat sheets** for the LLM — they do not replace the base file.

### 1. `config/action_ids/` — “what kind of step is this?”

An **Action ID** is a reusable step type on the Edwin platform (Create incident, Delay, Update alert, …). Many steps in the base YAML share the same Action ID.

**Example:** the step *“Create ServiceNow Incident linked to this alert”* uses Action ID `create-snc-incident`.

`action_ids/` tells the LLM how to patch that type:

| File | Role | Example |
|------|------|---------|
| `field_sets.yaml` | Shared field names used across types | `caller_id` → “Edwin Integration” |
| `action_ids.yaml` | One entry per Action ID type | For `create-snc-incident`: patch `caller_id`; use `add_step_precondition_conditions` for severity rules |

So if the user says *“set caller_id to Edwin Integration”*, the LLM knows which patch type and field apply — without re-reading all 2,000 lines of base YAML.

### 2. `config/action_group/` — “which part of this workflow are we talking about?”

The **action group** is this whole LM Alert Processing workflow. We split its steps into **step groups** so guided setup can ask a few focused questions (max 2 per group).

**Example:** steps *“Create a new alert…”* through *“Update Singleton Alert Escalation…”* belong to group `alert_intake_path`. That group asks things like *“Should SDT steps be kept or removed?”* (key: `alert_intake_path__sdt_handling`).

| File | Role |
|------|------|
| `lm_alert_processing_step_groups.yaml` | Six groups: step names in each group + sample questions |

**Action IDs = patch rules by step type. Action group = question groups for this workflow.**

Full workflow YAML: `inputs/lm_alert_processing_base.yaml` (not duplicated here).

---

## Guided setup flow

```text
1. Read base YAML
2. Build prompt from prompts/question_generation.j2
   + action_ids context + action_group context + base YAML
3. LLM returns JSON questions (keys like alert_intake_path__sdt_handling)
4. User answers in Streamlit
5. Build prompt from prompts/yaml_patch_generation.j2 + answers
6. LLM returns patch JSON
7. core/yaml_patches.py applies patches
8. core/yaml_validation.py checks shape
9. Save final.yaml
```

---

## What to edit when

| Goal | Edit |
|------|------|
| Add / change reusable Action ID guidance | `config/action_ids/action_ids.yaml`, `field_sets.yaml` |
| Add / change guided question groups | `config/action_group/lm_alert_processing_step_groups.yaml` |
| Change LLM instructions or examples | `prompts/question_generation.j2`, `prompts/yaml_patch_generation.j2` |
| Tighten what patches Python allows | `config/constants.py`, `core/yaml_patches.py`, `core/yaml_validation.py` |
| Change default base file path | `config/constants.py` (`DEFAULT_BASE_YAML_PATH`) |

---

## Public API (imports)

From `ai_workflow.action_groups.lm_alert_processing`:

- `LMAlertProcessingCustomizer` — run the full flow
- `build_lm_alert_action_id_*` — Action ID prompt context
- `build_lm_alert_action_group_*` — step group prompt context
- `apply_yaml_patches`, `validate_final_lm_alert_yaml` — apply and check output

Older names (`build_lm_alert_action_schemas`, `build_lm_alert_step_groups`, …) still work as aliases.

---

## Tests

```bash
.venv/bin/python -m pytest tests/test_lm_alert_processing_customizer.py -q
```
