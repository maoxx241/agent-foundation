# WRITEBACK_RULES

## 1. Purpose

Writeback converts validated task outcomes into:
- memory updates
- candidate thin-KB objects

Writeback is not equivalent to automatic publication into trusted canonical knowledge.

## 2. Memory writeback

### Good candidates for memory
- user preferences discovered during the task
- stable project preferences
- recurring context likely needed in future sessions
- short summaries of important recent decisions

### Bad candidates for memory
- full artifact bodies
- detailed patch contents
- long benchmark tables
- noisy logs
- speculative conclusions

## 3. Thin KB writeback

Phase 1 allows writeback proposals for:
- Claim
- Procedure
- Case
- Decision

These are proposals only.

## 4. Promotion criteria

A writeback candidate should be considered promotable only if it is:
- reusable
- specific
- evidence-grounded
- not merely task-local
- still meaningful outside the current chat session

## 5. Mapping

### ExperiencePacket -> Claim
Use when a task yields a reusable factual statement with supporting evidence.

### ExperiencePacket -> Procedure
Use when the fix or method is repeatable by following clear steps.

### ExperiencePacket -> Case
Use when the incident or experiment itself is worth future lookup.

### ExperiencePacket -> Decision
Use when the task yields a reusable architectural or workflow decision.

## 6. Phase 1 policy

Phase 1 does not automatically mark anything as trusted.
All promoted objects are created as candidate unless explicitly reviewed by a later process.
