# Mem0 integration notes

## Scope

Phase 1 does not reimplement memory.
It uses the Mem0 integration for OpenClaw as the Memory Plane.

## Memory policy

Allowed into memory:
- user preferences
- long-lived project facts
- recent context summaries
- stable recurring facts likely useful across sessions

Not allowed into memory by default:
- full design drafts
- raw patch contents
- benchmark raw tables
- transient execution logs
- canonical engineering truth that should live in Thin KB later

## Operational scopes

Recommended logical keys:
- user_id = q
- project_id = <project-name>
- run_id = <task_id>

Recommended memory buckets:
- user-long-term
- project-shared
- session-or-task

## OpenClaw tools

Use the Mem0-provided tools:
- memory_search
- memory_store
- memory_get
- memory_list
- memory_forget

## Guardrails

- Memory is not an audit log.
- Memory is not the active task source of truth.
- Memory is not the canonical KB.
- High-value memories should be summarized, not copied verbatim from long artifacts.
