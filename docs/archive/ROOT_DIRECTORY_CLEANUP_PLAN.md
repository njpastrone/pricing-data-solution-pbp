# Root Directory Cleanup Plan

**Created:** 2026-01-20
**Status:** Ready for Review
**Goal:** Organize root directory files into appropriate subdirectories

---

## Current State Analysis

**Total Files in Root:** 15 markdown files + 1 text file + production files
**Total Size:** ~170 KB of documentation in root

### File Categories

#### ✅ Keep in Root (Essential)
These files MUST stay in the root directory:

1. **Production Code & Config:**
   - `app.py` (476 KB) - Main application
   - `requirements.txt` - Python dependencies
   - `start.sh` - Render deployment script
   - `.gitignore` - Git configuration
   - `.mcp.json` - Claude Code configuration

2. **Core Documentation (User-Facing):**
   - `README.md` (23 KB) - Project overview & quick start
   - `CLAUDE.md` (56 KB) - Project rules & AI assistant context
   - `CHANGELOG.md` (13 KB) - Version history

3. **Active Development Tracking:**
   - `ACTIVE_DEVELOPMENT_TODO.md` (4.1 KB) - Current sprint tasks

4. **Schema Documentation:**
   - `SCHEMA_UPDATE_PROCESS.md` (14 KB) - Systematic schema update guide
   - `schema_reference.md` (5.3 KB) - Current schema reference

#### 🗂️ Move to docs/testing/ (Testing Documentation)
Testing guides and checklists should be organized with other test docs:

1. `CHROME_TESTING_GUIDE.md` (13 KB)
   - **Current:** Root directory
   - **Move to:** `docs/testing/CHROME_TESTING_GUIDE.md`
   - **Reason:** Browser-specific testing guide belongs with other test documentation

2. `SCHEMA_UPDATE_TEST_GUIDE.md` (5.0 KB)
   - **Current:** Root directory
   - **Move to:** `docs/testing/SCHEMA_UPDATE_TEST_GUIDE.md`
   - **Reason:** Testing guide for schema validation

3. `test_results_summary.txt` (950 bytes)
   - **Current:** Root directory
   - **Move to:** `docs/testing/test_results_summary.txt` OR `scripts/features/test_results_summary.txt`
   - **Reason:** Test results belong with testing documentation or test scripts

#### 📦 Move to docs/archive/ (Completed Features)
Implementation docs for completed features:

1. `BUGFIX_CUSTOMIZATION_ADDONS_DISPLAY.md` (4.4 KB)
   - **Current:** Root directory
   - **Move to:** `docs/archive/BUGFIX_CUSTOMIZATION_ADDONS_DISPLAY.md`
   - **Reason:** Bug fix documentation for completed work (v7.5.0)
   - **Status:** Feature complete, kept for historical reference

2. `CUSTOMIZATION_ADDONS_UPDATE.md` (3.7 KB)
   - **Current:** Root directory
   - **Move to:** `docs/archive/CUSTOMIZATION_ADDONS_UPDATE.md`
   - **Reason:** Implementation notes for completed Customization Add-Ons feature
   - **Status:** Feature complete (v7.5.0)

3. `TAB5_FINAL_VERIFICATION.md` (5.0 KB)
   - **Current:** Root directory
   - **Move to:** `docs/archive/TAB5_FINAL_VERIFICATION.md`
   - **Reason:** Tab 5 no longer exists (app uses 4-tab structure)
   - **Status:** Obsolete documentation

4. `TAB5_STRESS_TEST_CHECKLIST.md` (9.4 KB)
   - **Current:** Root directory
   - **Move to:** `docs/archive/TAB5_STRESS_TEST_CHECKLIST.md`
   - **Reason:** Tab 5 no longer exists (app uses 4-tab structure)
   - **Status:** Obsolete documentation

#### 📋 Move to docs/planning/ (Planning Documentation)

1. `EXEC_PRICING_TOOL_IMPLEMENTATION_PLAN.md` (10 KB)
   - **Current:** Root directory
   - **Move to:** `docs/planning/EXEC_PRICING_TOOL_IMPLEMENTATION_PLAN.md`
   - **Reason:** Planning document for a feature (may be in progress or complete)
   - **Status:** Review to determine if active or should go to archive

#### 📝 Move to docs/meetings/ (Meeting Notes)

1. `RAW_MEETING_NOTES_01_13_25.md` (1.7 KB)
   - **Current:** Root directory
   - **Move to:** `docs/meetings/RAW_MEETING_NOTES_01_13_25.md`
   - **Reason:** Meeting notes belong with other meeting documentation
   - **Status:** Active meeting notes (January 13, 2025)

#### 🤔 Review & Decide

1. `SAVED_PROMPTS.md` (2.2 KB)
   - **Current:** Root directory
   - **Options:**
     - A) Move to `docs/SAVED_PROMPTS.md` (general reference)
     - B) Move to `docs/archive/SAVED_PROMPTS.md` (if outdated)
     - C) Keep in root if actively used
   - **Action:** Review contents to determine current relevance

#### 🗑️ Delete (System/Temporary Files)

1. `__pycache__/` directory
   - **Action:** Delete (will regenerate automatically)
   - **Command:** `rm -rf __pycache__/`
   - **Reason:** Python bytecode cache, not needed in version control

2. `.DS_Store` file
   - **Action:** Already in .gitignore, safe to delete
   - **Command:** `rm .DS_Store`
   - **Reason:** macOS system file

---

## Cleanup Actions

### Phase 1: Move Testing Documentation (3 files)

```bash
# Create testing directory if needed (already exists)
mkdir -p docs/testing

# Move testing guides
mv CHROME_TESTING_GUIDE.md docs/testing/
mv SCHEMA_UPDATE_TEST_GUIDE.md docs/testing/
mv test_results_summary.txt docs/testing/
```

### Phase 2: Archive Completed Work (4 files)

```bash
# Move to archive
mv BUGFIX_CUSTOMIZATION_ADDONS_DISPLAY.md docs/archive/
mv CUSTOMIZATION_ADDONS_UPDATE.md docs/archive/
mv TAB5_FINAL_VERIFICATION.md docs/archive/
mv TAB5_STRESS_TEST_CHECKLIST.md docs/archive/
```

### Phase 3: Organize Planning & Meeting Docs (2 files)

```bash
# Review and move (after checking if still active)
mv EXEC_PRICING_TOOL_IMPLEMENTATION_PLAN.md docs/planning/  # or docs/archive/ if complete

# Move meeting notes
mv RAW_MEETING_NOTES_01_13_25.md docs/meetings/
```

### Phase 4: Review SAVED_PROMPTS.md (1 file)

```bash
# Option A: Move to docs/ as general reference
mv SAVED_PROMPTS.md docs/SAVED_PROMPTS.md

# Option B: Archive if outdated
# mv SAVED_PROMPTS.md docs/archive/SAVED_PROMPTS.md

# Option C: Keep in root if actively used
# (no action needed)
```

### Phase 5: Clean System Files

```bash
# Delete Python cache
rm -rf __pycache__/

# Delete macOS system file (optional, already ignored)
rm .DS_Store
```

---

## Expected Result

### Root Directory (After Cleanup)

**Production Files:**
- app.py
- requirements.txt
- start.sh
- .gitignore
- .mcp.json
- .streamlit/

**Core Documentation:**
- README.md
- CLAUDE.md
- CHANGELOG.md
- ACTIVE_DEVELOPMENT_TODO.md

**Schema Documentation:**
- SCHEMA_UPDATE_PROCESS.md
- schema_reference.md

**Directories:**
- src/
- scripts/
- docs/
- templates/
- backups/
- data/
- config/
- .git/, .github/, .claude/

**Total Markdown Files in Root:** 6 (down from 15)
**Reduction:** 60% fewer files in root

---

## Git Commit Strategy

### Option A: Single Commit (Recommended)
```bash
git add -A
git commit -m "REFACTOR: Clean up root directory - move docs to appropriate subdirectories

Moved Files:
- Testing docs → docs/testing/ (3 files)
- Completed features → docs/archive/ (4 files)
- Planning docs → docs/planning/ (1 file)
- Meeting notes → docs/meetings/ (1 file)

Deleted:
- __pycache__/ (Python cache)
- .DS_Store (macOS system file)

Result: 60% reduction in root directory clutter (15 → 6 markdown files)"
```

### Option B: Phased Commits (if you prefer granular history)
```bash
# Commit 1: Archive completed work
git add docs/archive/
git commit -m "REFACTOR: Archive completed feature docs"

# Commit 2: Organize testing docs
git add docs/testing/
git commit -m "REFACTOR: Move testing docs to docs/testing/"

# Commit 3: Organize planning/meetings
git add docs/planning/ docs/meetings/
git commit -m "REFACTOR: Move planning and meeting docs to appropriate folders"

# Commit 4: Clean system files
git add .
git commit -m "REFACTOR: Remove Python cache and system files"
```

---

## Benefits

1. **Clearer Root Directory**
   - Only essential production files and core documentation remain
   - Easier to find critical files (README, CLAUDE, app.py)
   - Better first impression for new contributors

2. **Better Organization**
   - Testing docs consolidated in docs/testing/
   - Completed work archived in docs/archive/
   - Meeting notes organized in docs/meetings/
   - Planning docs in docs/planning/

3. **Follows Best Practices**
   - Root directory contains only essentials
   - Documentation organized by type and status
   - Clear separation: active vs. archived

4. **Improved Maintenance**
   - Easier to find relevant documentation
   - Clear file lifecycle (active → archive)
   - Reduced clutter when opening project

---

## Risks & Considerations

### Potential Issues

1. **Broken Links**
   - Some docs may reference root-level files
   - **Mitigation:** Search for references before moving, update links

2. **Git History**
   - Moving files preserves history in git
   - **Mitigation:** Use `git mv` if you want explicit move tracking

3. **External References**
   - Documentation might be linked from external sources
   - **Mitigation:** Keep README.md, CLAUDE.md, CHANGELOG.md in root (most commonly linked)

### Pre-Cleanup Checklist

- [ ] Review SAVED_PROMPTS.md contents (decide keep vs. move)
- [ ] Check if EXEC_PRICING_TOOL_IMPLEMENTATION_PLAN.md is active or complete
- [ ] Search for internal references to files being moved
- [ ] Ensure docs/testing/, docs/archive/, docs/planning/, docs/meetings/ directories exist
- [ ] Create backup commit before starting

---

## Next Steps

1. **Review this plan** - Confirm all moves make sense
2. **Create backup commit** - Just in case
3. **Execute Phase 1-5** - Move files systematically
4. **Test links** - Verify no broken references
5. **Commit changes** - Use appropriate commit message
6. **Push to remote** - Deploy cleaned structure

---

## Questions to Answer Before Cleanup

1. **Is SAVED_PROMPTS.md still actively used?**
   - If yes: Keep in root
   - If no: Move to docs/ or archive

2. **Is EXEC_PRICING_TOOL_IMPLEMENTATION_PLAN.md active or complete?**
   - If active: Move to docs/planning/
   - If complete: Move to docs/archive/

3. **Should test_results_summary.txt go to docs/testing/ or scripts/features/?**
   - docs/testing/ = documentation perspective
   - scripts/features/ = near the test scripts

4. **Do you want a single commit or phased commits?**
   - Single commit = cleaner history
   - Phased commits = easier to review/revert

---

**Ready to execute?** Review the questions above, then run the cleanup phases.
