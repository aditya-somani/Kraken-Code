---
description: How to resume work after a break or new session
---

# Resuming Development

// turbo-all

1. Read AI instructions
```bash
cat .agent/memory/INSTRUCTIONS.md
```

2. Read status
```bash
cat .agent/memory/README.md
```

3. Read current session
```bash
cat .agent/memory/current_session.md 2>/dev/null || echo "New project - run onboarding"
```

4. Check pending questions
```bash
cat .agent/memory/questions/pending.md
```

5. Continue from "Next Action" in README
