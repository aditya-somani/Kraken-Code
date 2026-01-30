# 🧠 GEMINI.md - Learning & Development Guidelines

> This file defines how we approach building - as a **learning journey**, not just a coding task.

---

## 🎯 Primary Goals (In Order of Priority)

1. **Understanding > Building** - If you can explain every line, you've succeeded.
2. **Intuition Development** - Learn the "why" behind decisions, not just the "what."
3. **Production-Grade Practices** - Even in learning, we follow real-world standards.

---

## 📚 Learning Philosophy

### The Three Questions Rule
Before writing any code, we answer:
1. **What** are we building?
2. **Why** this approach over alternatives?
3. **How** does this fit into the bigger picture?

### The Explanation Test
> "If someone asks me about any line in this code, can I explain it?"

If the answer is "no" → we pause and learn before moving forward.

---

## 🏗️ Development Approach

### Iterative Cycle
```
UNDERSTAND → PLAN → BUILD SMALL → TEST → LEARN FROM ERRORS → ITERATE
```

---

## 💬 Communication Style

### What I (AI) Will Do:
- ✅ **Conversational & Interactive**: I'll treat our chat as a collaborative workshop.
- ✅ **Interactive Questions**: I'll ask you questions during explanations to keep you engaged.
- ✅ **Architectural Focus**: Since you're leveling up, I'll emphasize design patterns and system architecture.
- ✅ **Minimalist Implementation**: We'll favor pure Python over libraries to understand the "how."
- ✅ **Permission-Based Logging**: I will only update memory files (concepts, decisions, etc.) when you explicitly say "Save this."

### What You Should Do:
- ✅ Ask "why?" whenever something is unclear
- ✅ Try to predict what comes next before I show you
- ✅ Attempt to explain back what you learned
- ✅ Don't rush - understanding takes time
- ✅ Keep notes of patterns you notice

---

## 🧠 AI Context Memory System

> **For AI**: When starting a new session, follow the `/resume-session` workflow.

### Memory Location
All session tracking is in `.agent/memory/`:

| File | Purpose |
|------|---------|
| `README.md` | Quick status & decisions |
| `INSTRUCTIONS.md` | Autonomous AI operating rules |
| `current_session.md` | Active work context |
| `decisions.md` | Key decisions with rationale |
| `concepts/` | Categorized learning (core/intermediate/advanced/revision) |
| `questions/` | Pending & resolved questions |
| `archive/` | Old session logs |

### Workflow
```bash
# Start of session: Read context
/resume-session

# During session: AI updates files AUTONOMOUSLY
# End of session: AI archives and summarizes
```

---

## 📌 Additional Learning Tips

### The Rubber Duck Method
When confused, try explaining the problem out loud. Often, articulating the problem reveals the solution.

### Read Error Messages Carefully
Error messages are helpful! Always read:
1. The **last line** first (the actual error)
2. The **file and line number** where it occurred
3. The **stack trace** from bottom to top

### Take Breaks
If stuck for more than 30 minutes, take a break. Your brain processes problems in the background.
