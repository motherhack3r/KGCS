# Quick Commands: Repository Utilities

**Status:** The `refactor/clean-structure` branch has been merged into `devel` (January 25, 2026).

## Cleanup Workspace

```bash
# Show items that would be cleaned (always safe)
python scripts/cleanup_workspace.py

# Clean temporary files and cache
python scripts/cleanup_workspace.py --execute

# Preview without deleting
python scripts/cleanup_workspace.py --dry-run

# Include downloaded source data
python scripts/cleanup_workspace.py --sources --execute

# Include transformed sample data  
python scripts/cleanup_workspace.py --data --execute

# Everything at once
python scripts/cleanup_workspace.py --sources --data --execute
```

## Merge to Main

```bash
# Switch to main
git checkout main
git pull origin main

# Merge the branch
git merge refactor/clean-structure

# OR create a PR (GitHub)
git push origin refactor/clean-structure
# Then open PR in browser
```

## View Git History

```bash
# See commits on this branch
git log --oneline refactor/clean-structure -10

# Compare with base
git log --oneline roadmap/phase3..refactor/clean-structure

# View commit details
git show 7ddb173      # Main refactor commit
git show da63ad7      # Branch summary commit
git show 8e3dbfe      # Status overview commit
```

## Restore Archived Files (if needed)

```bash
# List archived files
git ls-tree -r HEAD docs/.archive/

# Restore a single file
git show refactor/clean-structure:docs/.archive/draft-20260125/mini-draft.md > mini-draft.md

# Restore entire archived folder
git checkout refactor/clean-structure -- docs/.archive/draft-20260125/
```

## What Changed (Summary)

```
✅ Archived (preserved in git):
   - docs/draft/          (9 files)
   - docs/wip-status/     (5 files)
   - docs/agent/          (5 files)
   → All moved to: docs/.archive/[folder]-20260125/

✨ Created (new):
   - docs/ARCHITECTURE.md  (5-phase roadmap)
   - docs/GLOSSARY.md      (Standards reference)
   - docs/EXTENDING.md     (Extension guide)
   - docs/DEPLOYMENT.md    (Setup guide)
   - BRANCH-SUMMARY.md     (Refactor summary)
   - REFACTOR-STATUS.md    (This status overview)

🔐 Unchanged (fully functional):
   - src/          (All code)
   - tests/        (All tests)
   - scripts/      (All utilities)
   - docs/ontology/ (Ontologies, SHACL, RAG)
   - .github/      (CI/CD)
```

## Branch Statistics

```
Branch:     refactor/clean-structure
Base:       roadmap/phase3
Commits:    3
Files:      24 changed (18 renamed, 6 new files)
Insertions: +2,271
Status:     ✅ Ready for merge
Conflicts:  ❌ None
```

## Next Steps After Merge

```bash
# After merging to main:

1. Confirm merge succeeded
   git log --oneline main -3

2. Update local branches
   git checkout main
   git pull origin main

3. Delete old branch
   git branch -d refactor/clean-structure
   git push origin --delete refactor/clean-structure

4. Begin Phase 3 MVP
   # Use DEPLOYMENT.md to start Neo4j integration
```

## Troubleshooting

**Q: Branch has conflicts?**
```bash
# This shouldn't happen, but if it does:
git merge --abort
git rebase roadmap/phase3
git push --force origin refactor/clean-structure
```

**Q: Want to see exactly what changed in a file?**
```bash
git diff roadmap/phase3..HEAD -- docs/ARCHITECTURE.md
```

**Q: Need to revert the merge later?**
```bash
git revert -m 1 <merge-commit-hash>
```

**Q: How to cherry-pick specific changes?**
```bash
# Cherry-pick just the docs/GLOSSARY.md creation
git cherry-pick 7ddb173  # Main commit
```

---

## Key Files to Review

| File | Lines | Purpose |
| --- | --- | --- |
| **REFACTOR-STATUS.md** | 270 | ← Start here (this file) |
| **BRANCH-SUMMARY.md** | 288 | Detailed branch info |
| **docs/ARCHITECTURE.md** | 285 | 5-phase roadmap |
| **docs/GLOSSARY.md** | 320 | Standards reference |
| **docs/EXTENDING.md** | 310 | How to add standards |
| **docs/DEPLOYMENT.md** | 475 | Setup guide |

---

## Summary

✅ **Branch is complete and ready for:**
1. Code review
2. Testing
3. Merging to main
4. Proceeding with Phase 3 MVP

All functionality preserved. Zero breaking changes. Full git history maintained.

**Start with:** `cat docs/ARCHITECTURE.md`

