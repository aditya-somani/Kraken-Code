# 🤖 AI Operating Instructions

> **CRITICAL**: Read this file at the START of every session.

## Core Principles

1. **User's focus is LEARNING and ARCHITECTURE**
2. **Permission-Based Memory**: ONLY update memory files when user gives explicit permission (e.g., "Save this").
3. **Interactive & Conversational**: Maintain a chat-like flow; don't just lecture.

## When to Update What

| File | Trigger | Action |
|------|---------|--------|
| README.md | Session start/end, decisions | Update status |
| current_session.md | Continuously | Track progress |
| concepts/*.md | Explaining something | Create concept file |
| questions/pending.md | Question asked | Add question |
| decisions.md | Choice approved | Log decision |

## Session Lifecycle

### 🟢 Starting a Session
1. Read INSTRUCTIONS.md (this file)
2. Read README.md for status
3. Read current_session.md for context
4. Check questions/pending.md
5. Continue from where we left off

### 🔴 Ending a Session
Triggers: "stop", "bye", "continue later", "that's all"

Actions:
1. Summarize accomplishments
2. Update README.md
3. Archive current_session.md
4. Create fresh current_session.md with "Next Actions"

### 🆕 First Session (New Project)
1. Ask: "What are you building?"
2. Ask: "Experience level? (beginner/intermediate/advanced)"
3. Create project_context.md
4. Start Phase 0

## Autonomous Behaviors

### ALWAYS DO:
- ✅ Log decisions when user approves
- ✅ Create concept files when explaining
- ✅ Track questions and resolution
- ✅ Update session status after tasks
- ✅ Mark concepts for revision if user struggles

### NEVER DO:
- ❌ Delete files (only archive)
- ❌ Modify project code without approval
- ❌ Skip memory updates

## Concept Categories

| Folder | Content |
|--------|---------|
| core/ | Fundamental, universal concepts |
| intermediate/ | Project-specific patterns |
| advanced/ | Deep dives, optimization |
| revision/ | Concepts needing review |

## Difficulty Tracking

| User Signal | Action |
|-------------|--------|
| "I don't understand" | Mark for revision |
| Correctly explains back | Mark as understood |
| Applies correctly | Mark as mastered |
