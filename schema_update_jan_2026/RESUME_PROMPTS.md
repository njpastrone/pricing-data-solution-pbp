# Schema Transition - Resume Work Prompts

**Purpose:** Perfect prompts to resume work on any phase of the schema transition.

**Usage:** Copy the prompt for your current phase and paste it into a new Claude conversation.

---

## 📋 Phase 1: Core Pricing Engine

```
I'm continuing work on the PBP schema transition (January 2026) - Phase 1: Core Pricing Engine.

**Context Files to Read:**
1. schema_update_jan_2026/MASTER_TRACKING.md - Complete context and decisions
2. schema_update_jan_2026/PHASE1_PRICING_ENGINE_GUIDE.md - Implementation guide for this phase
3. schema_reference.md - New schema definition (44 columns)

**Quick Context:**
- Major schema transition: 33 columns → 44 columns
- Discussion phase complete (8 decisions made)
- Implementing 3 new pricing methods: "MSRP + % of cost", "MSRP capped – ship absorbed", "Standard markup"
- Cost basis system: Per Item vs Per Package normalization
- Hybrid validation: Read spreadsheet + calculate for comparison

**Current Phase:** Phase 1 - Core Pricing Engine
**Status:** [Starting fresh / In progress at step X / Completing final tests]

**Files to Modify:**
- src/helpers.py (column mappings, normalization, pricing logic helpers)
- src/pricing_engine.py (3 pricing methods, validation, diagnostic markups)

**Task:** Implement the new pricing calculation engine following PHASE1_PRICING_ENGINE_GUIDE.md step-by-step.

Please confirm you've read the context files and understand Phase 1 scope before we begin.
```

---

## 🎨 Phase 2: UI Updates (Tab 1)

```
I'm continuing work on the PBP schema transition (January 2026) - Phase 2: UI Updates (Tab 1).

**Context Files to Read:**
1. schema_update_jan_2026/MASTER_TRACKING.md - Complete context and decisions
2. schema_update_jan_2026/PHASE2_UI_UPDATES_GUIDE.md - Implementation guide for this phase
3. schema_reference.md - New schema definition (44 columns)

**Quick Context:**
- Phase 1 (Core Pricing Engine) is COMPLETE
- New pricing methods implemented: MSRP + %, MSRP capped, Standard markup
- Cost normalization working (Per Item vs Per Package)
- Validation comparing spreadsheet vs calculated values

**Current Phase:** Phase 2 - UI Updates (Tab 1 - Proposal Generator)
**Status:** [Starting fresh / In progress / Completing final tests]

**Files to Modify:**
- app.py (Tab 1 sections)
- Focus on product catalog, proposal configuration, pricing display, MSRP checkbox

**Task:** Update Tab 1 UI to use new pricing logic, display validation results, show pricing notes, and add manual override checkbox.

Please confirm you've read the context files and understand Phase 2 scope before we begin.
```

---

## 🛒 Phase 3: UI Updates (Tab 3)

```
I'm continuing work on the PBP schema transition (January 2026) - Phase 3: UI Updates (Tab 3).

**Context Files to Read:**
1. schema_update_jan_2026/MASTER_TRACKING.md - Complete context and decisions
2. schema_update_jan_2026/PHASE3_UI_UPDATES_GUIDE.md - Implementation guide for this phase
3. schema_reference.md - New schema definition (44 columns)

**Quick Context:**
- Phase 1 (Core Pricing Engine) is COMPLETE
- Phase 2 (Tab 1 UI) is COMPLETE
- New pricing methods working in Tab 1
- Manual override checkbox implemented

**Current Phase:** Phase 3 - UI Updates (Tab 3 - Order & Client Info)
**Status:** [Starting fresh / In progress / Completing final tests]

**Files to Modify:**
- app.py (Tab 3 sections)
- Focus on order item pricing, manual product addition, price warnings, notes display

**Task:** Update Tab 3 UI to use new pricing logic consistently with Tab 1, maintain manual override functionality, show validation results.

Please confirm you've read the context files and understand Phase 3 scope before we begin.
```

---

## 📄 Phase 4: UI Updates (Tab 4)

```
I'm continuing work on the PBP schema transition (January 2026) - Phase 4: UI Updates (Tab 4).

**Context Files to Read:**
1. schema_update_jan_2026/MASTER_TRACKING.md - Complete context and decisions
2. schema_update_jan_2026/PHASE4_UI_UPDATES_GUIDE.md - Implementation guide for this phase
3. schema_reference.md - New schema definition (44 columns)

**Quick Context:**
- Phase 1 (Core Pricing Engine) is COMPLETE
- Phase 2 (Tab 1 UI) is COMPLETE
- Phase 3 (Tab 3 UI) is COMPLETE
- All pricing logic working across Tab 1 and Tab 3

**Current Phase:** Phase 4 - UI Updates (Tab 4 - Execution & Accounting)
**Status:** [Starting fresh / In progress / Completing final tests]

**Files to Modify:**
- app.py (Tab 4 sections)
- Focus on invoice generation, description field usage (Billing vs Purchase), CSV exports

**Task:** Update Tab 4 to use correct description fields per use case (invoices vs POs), verify pricing matches Tab 3, clean display (no pricing notes).

Please confirm you've read the context files and understand Phase 4 scope before we begin.
```

---

## 🧪 Phase 5: Testing & Validation

```
I'm continuing work on the PBP schema transition (January 2026) - Phase 5: Testing & Validation.

**Context Files to Read:**
1. schema_update_jan_2026/MASTER_TRACKING.md - Complete context and decisions
2. schema_update_jan_2026/PHASE5_TESTING_GUIDE.md - Implementation guide for this phase
3. schema_reference.md - New schema definition (44 columns)

**Quick Context:**
- All UI phases complete (Phases 1-4)
- New pricing logic implemented across entire app
- 3 pricing methods working: MSRP + %, MSRP capped, Standard markup
- Manual override checkbox available
- Validation comparing spreadsheet vs calculated values

**Current Phase:** Phase 5 - Testing & Validation
**Status:** [Starting fresh / Running tests / Fixing bugs / Final verification]

**Files to Modify:**
- Test scripts in scripts/features/
- Potentially bug fixes in src/ and app.py

**Task:** Comprehensive testing of all pricing methods, validation logic, empty field handling, description fallbacks, and full workflow (Tab 1 → Tab 4).

Please confirm you've read the context files and understand Phase 5 scope before we begin.
```

---

## 📚 Phase 6: Documentation & Deployment

```
I'm continuing work on the PBP schema transition (January 2026) - Phase 6: Documentation & Deployment.

**Context Files to Read:**
1. schema_update_jan_2026/MASTER_TRACKING.md - Complete context and decisions
2. schema_update_jan_2026/PHASE6_DOCUMENTATION_GUIDE.md - Implementation guide for this phase
3. schema_reference.md - New schema definition (44 columns)

**Quick Context:**
- All phases complete (Phases 1-5)
- Testing passed
- App working with new schema
- Ready to document and deploy

**Current Phase:** Phase 6 - Documentation & Deployment
**Status:** [Starting fresh / Updating docs / Preparing deployment / Complete]

**Files to Modify:**
- CHANGELOG.md (comprehensive update)
- docs/planning/METHODOLOGY_LOGIC.md (new pricing methods)
- README.md (version update)
- CLAUDE.md (remove schema transition notice)

**Task:** Update all documentation to reflect completed schema transition, prepare deployment checklist, update methodology docs with new pricing logic.

Please confirm you've read the context files and understand Phase 6 scope before we begin.
```

---

## 🚨 Emergency: Lost Context Mid-Phase

```
I lost context in the middle of working on the PBP schema transition (January 2026).

**Last Known Status:**
- Phase: [Which phase were you working on?]
- Task: [What specific task were you doing?]
- Files Modified: [Which files did you already change?]
- Issue: [What problem occurred that caused context loss?]

**Context Recovery:**
Please read these files to recover context:
1. schema_update_jan_2026/MASTER_TRACKING.md - Complete overview
2. schema_update_jan_2026/PHASE[X]_[NAME]_GUIDE.md - Current phase guide
3. Check git status to see what files are modified

**Request:**
Please help me understand where I left off and what the next step should be. Read the tracking document and current phase guide, then let's review what's been done so far.

[Paste any error messages or specific issues here]
```

---

## 💡 General Resume (Any Phase)

```
I'm resuming work on the PBP pricing app schema transition (January 2026).

**Context Location:**
All documentation is in: schema_update_jan_2026/

**Start Here:**
1. Read schema_update_jan_2026/MASTER_TRACKING.md
2. Check Status Log section to see current phase
3. Read the phase guide for current phase

**Project Context:**
- Major schema overhaul: 33 → 44 columns
- 3 new pricing methods replacing simple markup
- Cost basis system (Per Item vs Per Package)
- Hybrid validation (spreadsheet + calculated)

**Current Status:**
I'm not sure which phase I'm on. Please read MASTER_TRACKING.md Status Log and tell me:
- What phase we're currently on
- What's been completed
- What's the next task

Then let's continue from there.
```

---

## 📝 Usage Tips

1. **Always specify which phase you're on** - this helps Claude load the right context
2. **Mention if you're starting fresh vs continuing** - changes the level of detail needed
3. **Include any specific issues** - helps Claude understand blockers
4. **Reference the phase guide** - ensures implementation follows the plan
5. **Check git status first** - see what's already been modified

---

## 🔍 Quick Phase Lookup

| Phase | Focus | Files | Guide |
|-------|-------|-------|-------|
| 1 | Core Pricing Engine | src/helpers.py, src/pricing_engine.py | PHASE1_PRICING_ENGINE_GUIDE.md |
| 2 | UI Updates (Tab 1) | app.py (Tab 1 sections) | PHASE2_UI_UPDATES_GUIDE.md |
| 3 | UI Updates (Tab 3) | app.py (Tab 3 sections) | PHASE3_UI_UPDATES_GUIDE.md |
| 4 | UI Updates (Tab 4) | app.py (Tab 4 sections) | PHASE4_UI_UPDATES_GUIDE.md |
| 5 | Testing & Validation | Test scripts, bug fixes | PHASE5_TESTING_GUIDE.md |
| 6 | Documentation | CHANGELOG, docs/ | PHASE6_DOCUMENTATION_GUIDE.md |

---

**END OF RESUME PROMPTS**
