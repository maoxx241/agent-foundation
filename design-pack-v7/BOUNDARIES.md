# BOUNDARIES

## 1. Core rule

Do not mix Memory, Task Artifacts, and Thin KB.

They serve different purposes and must remain separate.

## 2. Memory Plane

### Memory is for:
- user preferences
- stable personal facts
- project-level preferences or recurring context
- recent working context summaries
- things worth recalling across sessions

### Memory is not for:
- full design documents
- full test plans
- patch details
- benchmark raw outputs
- precise version matrices
- canonical incident truth

### Good memory examples
- The user prefers concise status reports.
- The user works primarily on inference/runtime optimization.
- The project commonly uses environment tuple X.
- Last week the team rejected approach B because of maintainability.

## 3. Task Artifact Plane

### Artifacts are for:
- current task source of truth
- explicit stage outputs
- reviewable, reproducible workflow material
- anything required for state transitions

### Artifacts are not for:
- cross-project general knowledge
- long-term personal memory
- generic reusable truths that have outlived the task

### Good artifact examples
- EvidencePack
- DesignSpec
- TestSpec
- PatchBundle
- ValidationReport
- ADR
- ExperiencePacket draft

## 4. Thin KB Plane

### Thin KB is for:
- reusable Claim
- reusable Procedure
- reusable Case
- reusable Decision

### Thin KB is not for:
- every raw task note
- noisy intermediate thoughts
- session-level chatter
- ephemeral details that are not worth reusing

### Good Thin KB examples
- A versioned compatibility claim
- A stable troubleshooting procedure
- A well-characterized incident case
- A reusable architectural decision

## 5. Promotion rules

### Memory -> Thin KB
Usually no direct promotion.
Memory is recall-oriented, not canonical by default.

### Artifacts -> Thin KB
Allowed when content is:
- reusable
- specific enough
- grounded in evidence
- still useful after the task ends

## 6. Truth hierarchy

For active work:
1. task artifacts
2. thin KB
3. memory

For user/project context:
1. memory
2. recent artifacts
3. thin KB if applicable

## 7. Role boundary summary

- OpenClaw work agents may read memory, artifacts, and thin KB.
- Work agents may write memory through memory tools.
- Work agents may write artifacts through artifact tools.
- Work agents must not directly write trusted canonical KB entries.
- Release/writeback is the only path that proposes promotion into Thin KB.
