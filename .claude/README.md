# Claude Code Project Scaffolding

This directory contains the Phase 0 scaffolding for the Darpan Labs What-If Simulator project. It ensures Claude Code operates with consistency, safety, and speed through automated guardrails and repeatability mechanisms.

## 📁 Directory Structure

```
.claude/
├── README.md                    # This file
├── claude.md                    # Main project instructions (CLAUDE.md)
├── lintconfig.json              # Lint rules and code quality standards
├── settings.local.json          # Local permissions and settings
├── commands/                    # Slash commands for common tasks
│   ├── check-determinism.md    # Scan for non-deterministic patterns
│   ├── run-gates.md            # Execute quality gates
│   ├── check-guards.md         # Verify ReasonGuard usage
│   ├── audit-config.md         # Find hardcoded parameters
│   ├── debug-loop.md           # Systematic debugging workflow
│   └── pre-commit.md           # Pre-commit validation checks
└── hooks/                       # Automated validation hooks
    ├── post-write.sh           # Runs after Write tool
    ├── pre-bash.sh             # Runs before Bash tool
    ├── post-edit.sh            # Runs after Edit tool
    └── pre-commit.sh           # Runs before git commit
```

## 🎯 Purpose

This scaffolding enforces three core principles:

1. **Consistency**: Deterministic behavior, standardized code style, configuration-driven parameters
2. **Safety**: Block dangerous operations, protect critical files, validate all changes
3. **Speed**: Automated checks, fast feedback loops, slash commands for common tasks

## 🔧 Components

### 1. lintconfig.json

Defines project-wide rules:
- **Determinism**: Enforce temperature=0, no random without seeds
- **Config-driven**: Model params must be in CONFIGS/, not hardcoded
- **Guard enforcement**: All LLM reasons must pass ReasonGuard
- **Comment style**: Explain WHY, not WHAT
- **Type hints**: All functions must have return type annotations

### 2. Slash Commands

Quick access to validation tasks:
- `/check-determinism` - Find non-deterministic code
- `/run-gates` - Check twin separation metrics
- `/check-guards` - Verify guard usage
- `/audit-config` - Find hardcoded parameters
- `/debug-loop` - Run systematic debugging
- `/pre-commit` - Full pre-commit validation

### 3. Hooks

Automated validation on tool usage:

**Post-write** (after creating/writing files):
- Auto-format with black
- Check determinism violations (ERROR)
- Verify type hints (WARNING)
- Check hardcoded parameters (WARNING)
- Ensure proper imports (INFO)

**Pre-bash** (before shell commands):
- Block destructive operations (rm -rf /, sudo)
- Protect critical files (twin_bank.json, git config)
- Enforce package manager consistency
- Prevent lockfile manual edits

**Post-edit** (after editing files):
- Check for introduced non-determinism (ERROR)
- Verify guard calls not removed (ERROR)
- Validate Python syntax
- Check for weakened test assertions

**Pre-commit** (before git operations):
- Full determinism check across codebase
- Run type checker (mypy)
- Verify guard usage in API code
- Run test suite (must pass)
- Check quality gates if twin logic modified

## 🚦 Hook Severity Levels

- **ERROR** 🚫: Blocks operation, must fix immediately
- **WARNING** ⚠️: Operation proceeds, should fix soon
- **INFO** ℹ️: Informational only, no action required

## 🎨 House Style Rules

### Comments
- Explain **WHY**, not **WHAT**
- Remove obvious comments that repeat code
- Keep comments that add context or explain trade-offs

### Configuration
- All model parameters in CONFIGS/
- No hardcoded model names, hyperparameters, or magic numbers
- Exception: test files can use literals

### Determinism
- Always `temperature=0` and `top_p=1`
- Set seed at entry points
- Canonical sorting: probability desc, then id asc
- No random operations without seed

### Type Hints
- All functions must have return type annotations
- Use `from __future__ import annotations`
- Keep imports ordered: future → stdlib → third-party → local

## 🐛 Debugging Loop

Systematic 5-step process for fixing issues:

1. **Enumerate Causes**: List 3-5 potential root causes
2. **Add Logging**: Strategic logs at key points
3. **Validate**: Test hypotheses one at a time
4. **Fix**: Apply minimal fix, verify with tests
5. **Clean Up**: Remove debug artifacts, update docs

## 📝 Usage Examples

### Run a slash command
```
/check-determinism
```

### Check quality before commit
```
/pre-commit
```

### Debug a failing test
```
/debug-loop
```

### Verify separation metrics
```
/run-gates
```

## ✅ Validation Checklist

Before committing code, ensure:
- [ ] No temperature != 0 in production code
- [ ] All LLM outputs go through ReasonGuard
- [ ] No hardcoded model parameters in src/
- [ ] Type hints present on all functions
- [ ] Comments explain WHY, not WHAT
- [ ] Tests pass: `make test`
- [ ] Quality gates pass: `make gate`
- [ ] Byte-identical output on repeated runs

## 🔍 File Protection

These files are protected and cannot be edited directly:
- `DATA/twin_bank.json` - Regenerate via distillation
- `.git/config` - Use git config commands
- Lockfiles (requirements.txt) - Update via package manager

## 🆘 Troubleshooting

### Hook blocks my operation
- Check the error message for the specific violation
- Fix the root cause (don't bypass hooks)
- If legitimate exception needed, discuss with team

### Slash command not found
- Ensure command file exists in `.claude/commands/`
- Check file has `.md` extension
- Restart Claude Code if recently added

### Hook runs too slow
- Most hooks complete in <1 second
- If slow, check for network operations or heavy computation
- Report performance issues to optimize

## 📚 Related Documentation

- [CLAUDE.md](claude.md) - Full project instructions
- [SPECS/WHAT_IF_SIMULATOR_SPEC.md](../SPECS/WHAT_IF_SIMULATOR_SPEC.md) - Engineering spec
- [README.md](../README.md) - Project overview and setup

## 🔄 Maintenance

### Adding a new hook
1. Create `.sh` file in `.claude/hooks/`
2. Make executable: `chmod +x hook-name.sh`
3. Follow naming: `pre-<tool>.sh` or `post-<tool>.sh`
4. Document in this README

### Adding a new slash command
1. Create `.md` file in `.claude/commands/`
2. Add description in frontmatter: `description: ...`
3. Write clear instructions for Claude to follow
4. Update command list in CLAUDE.md

### Updating lintconfig
1. Edit `.claude/lintconfig.json`
2. Test changes don't block valid code
3. Document new rules in CLAUDE.md
4. Announce to team if breaking change

---

**Built with guardrails for deterministic, safe, and fast AI coding.**
