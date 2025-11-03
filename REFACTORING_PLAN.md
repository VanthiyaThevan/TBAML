# Hackathon Project Refactoring Plan
## Goal: Lean & Mean Functional POC

**Date**: 2025-11-01  
**Objective**: Clean up project, remove duplicates, consolidate files, keep only essential POC functionality

---

## Analysis Summary

### Current State
- **Total Files**: ~100+ files
- **Core Application**: ✅ Well structured
- **Test Files**: ⚠️ Scattered (15+ test scripts)
- **Utility Scripts**: ⚠️ Many duplicates (8+ view/review scripts)
- **Documentation**: ⚠️ Fragmented (10+ .md files)
- **One-time Scripts**: ⚠️ Mixed with utilities

### Issues Identified
1. **Duplicate utility scripts**: Multiple view_*.py and review_*.py doing similar things
2. **Fragmented tests**: Test files scattered across root directory
3. **One-time scripts**: Scripts like `fix_confidence_scores.py` already executed
4. **Temporary files**: JSON exports, old data dumps
5. **Documentation bloat**: Multiple .md files that can be consolidated
6. **Generated files**: CSV exports, JSON dumps that should be in .gitignore

---

## Action Plan

### Phase 1: Remove One-Time Scripts ✅

**Files to Remove** (already executed, no longer needed):
- `fix_confidence_scores.py` - Database fix script (already run)
- `check_uc1_outputs.py` - One-time validation (if already checked)

**Action**: Move to archive or delete after verification

---

### Phase 2: Consolidate Duplicate Utility Scripts 🔄

**Duplicate View/Review Scripts** (consolidate into one):
- `view_database.py` ✅ (Keep - most comprehensive)
- `view_db_data.py` ❌ (Delete - duplicate)
- `view_collected_data.py` ❌ (Delete - duplicate)
- `view_scraped_content.py` ❌ (Delete - duplicate)
- `view_scraped_data.py` ❌ (Delete - duplicate)
- `view_full_data.py` ❌ (Delete - duplicate)
- `review_collected_data.py` ❌ (Delete - consolidate into view_database.py)
- `review_database_data.py` ❌ (Delete - consolidate into view_database.py)

**Action**: Keep `view_database.py`, enhance if needed, delete others

---

### Phase 3: Consolidate Test Files 📁

**Create `tests/` directory structure**:
```
tests/
├── __init__.py (exists)
├── test_stages.py (consolidate test_stage1/2/3.py)
├── test_api.py (move from root)
├── test_data_collection.py (consolidate integration tests)
├── test_website_discovery.py (keep)
└── test_tavily_fallback.py (keep)
```

**Files to Consolidate**:
- `test_stage1.py`, `test_stage2.py`, `test_stage3.py` → `tests/test_stages.py`
- `test_ofac_integration.py`, `test_eu_sanctions_integration.py`, `test_sec_integration.py` → `tests/test_data_collection.py`
- `test_ofac_parser.py` → `tests/test_data_collection.py`
- `test_api.py` → `tests/test_api.py` (move)
- `validate_stage3.py`, `validate_stage4.py` → `tests/test_stages.py` or delete if redundant

**Files to Keep Separately**:
- `test_website_discovery.py` (feature-specific)
- `test_tavily_fallback.py` (feature-specific)
- `test_real_companies.py` (useful for demos)

**Action**: Consolidate into tests/ directory structure

---

### Phase 4: Clean Up Temporary/Generated Files 🗑️

**Files to Remove** (generated/temporary):
- `data_review_20251101_102439.json` ❌ (temporary export)
- `database_review.json` ❌ (temporary export)
- `scraped_companies.json` ❌ (temporary export)
- `lob_verifications.csv` ❌ (can regenerate, add to .gitignore)
- `WhatsApp Image 2025-11-01 at 05.28.05.jpeg` ❌ (unnecessary)
- `Untitled.rtf` ❌ (old notes file)

**Action**: Delete temporary files, add generated files to .gitignore

---

### Phase 5: Consolidate Documentation 📚

**Keep Essential Docs**:
- `README.md` ✅ (Main project documentation)
- `PRODUCTION_READINESS_GAPS.md` ✅ (Important for future reference)

**Consolidate/Remove**:
- `PROJECT_PLAN.md` + `TASKS.md` → Merge into `README.md` or delete (outdated)
- `TECH_STACK.md` → Move content to `README.md`, delete file
- `CONFIDENCE_SCORE_FIX.md` → Archive or delete (historical)
- `DATA_SOURCES_REALITY_CHECK.md` → Consolidate into main docs
- `SEC_DATA_LIMITATIONS.md` → Move to inline code comments or `README.md`
- `EU_SANCTIONS_INTEGRATION.md` → Move to inline code comments or `README.md`
- `STAGE_3_4_COMPLETE.md` → Archive or delete (historical)
- `STAGE_4_VALIDATION_COMPLETE.md` → Archive or delete (historical)
- `TAVILY_FALLBACK_MECHANISM.md` → Keep in `docs/` or consolidate
- `WEBSITE_DISCOVERY_IMPLEMENTATION.md` → Keep in `docs/` or consolidate
- `HOW_TO_VALIDATE_API.md` → Move to `README.md` or delete

**Create**:
- `docs/ARCHITECTURE.md` (consolidate key architectural decisions)
- `docs/API.md` (API documentation)
- `docs/DEVELOPMENT.md` (development guide)

**Action**: Consolidate into essential docs, move feature docs to `docs/`

---

### Phase 6: Utility Scripts Review 🔧

**Keep** (useful for POC):
- `export_lob_to_csv.py` ✅ (useful utility)
- `refresh_database_with_real_data.py` ✅ (useful utility)
- `download_eu_sanctions.py` ✅ (data setup)
- `download_sec_tickers.py` ✅ (data setup)
- `list_tables.py` ✅ (useful utility)
- `update_uc1_outputs.py` ✅ (useful utility)

**Review/Delete**:
- `test_ai_with_real_data.py` → Move to `tests/` or consolidate
- `test_real_companies.py` → Move to `tests/` or keep if useful for demos

**Action**: Keep essential utilities, organize others

---

### Phase 7: Core Application Files ✅

**Keep All** (Essential POC functionality):
- `app/` directory (all modules) ✅
- `alembic/` directory ✅
- `frontend/` directory ✅
- `data/` directory (OFAC, EU, SEC data files) ✅
- `requirements.txt` ✅
- `alembic.ini` ✅
- `Dockerfile`, `docker-compose.yml` ✅
- `.env.example` ✅

**Action**: No changes needed

---

### Phase 8: Update .gitignore 🚫

**Add to .gitignore**:
- `*.csv` (generated exports)
- `*.json` (except package.json, tsconfig.json, etc.)
- `data_review_*.json`
- `database_review.json`
- `scraped_companies.json`
- `*.jpeg`, `*.jpg`, `*.png` (except assets)
- `*.rtf`

**Action**: Update .gitignore to exclude generated/temporary files

---

## Execution Plan

### Step 1: Backup Current State ✅
1. Create backup/archive directory
2. Move files we're removing to archive (just in case)

### Step 2: Remove One-Time Scripts ✅
1. Move `fix_confidence_scores.py` to archive (or delete)
2. Review `check_uc1_outputs.py` - delete if no longer needed

### Step 3: Consolidate View/Review Scripts 🔄
1. Review `view_database.py` - ensure it has all needed functionality
2. Delete duplicate view/review scripts
3. Test that remaining script works

### Step 4: Consolidate Tests 📁
1. Create tests/ directory structure
2. Move and consolidate test files
3. Update imports if needed
4. Test that tests still work

### Step 5: Clean Temporary Files 🗑️
1. Delete temporary JSON/CSV exports
2. Delete image files
3. Delete old notes files

### Step 6: Consolidate Documentation 📚
1. Merge content from multiple .md files into README.md or docs/
2. Move feature-specific docs to docs/ directory
3. Delete outdated/historical docs
4. Update README.md with essential information

### Step 7: Update .gitignore 🚫
1. Add patterns for generated files
2. Test that .gitignore works

### Step 8: Verify No Regressions ✅
1. Run all tests
2. Start application
3. Verify API endpoints work
4. Verify frontend works
5. Test data collection
6. Test AI analysis

---

## File Categories

### ✅ KEEP (Essential)
```
app/                    # Core application
alembic/                # Database migrations
frontend/               # Frontend application
data/                   # Data files (OFAC, EU, SEC)
requirements.txt        # Dependencies
alembic.ini             # Alembic config
Dockerfile              # Docker config
docker-compose.yml      # Docker compose
.env.example            # Environment template
README.md               # Main documentation
PRODUCTION_READINESS_GAPS.md  # Future reference

# Utilities
export_lob_to_csv.py
refresh_database_with_real_data.py
download_eu_sanctions.py
download_sec_tickers.py
list_tables.py
update_uc1_outputs.py
view_database.py        # Consolidated view script

# Tests (after consolidation)
tests/                  # Organized test suite
test_website_discovery.py
test_tavily_fallback.py
test_real_companies.py
```

### 🔄 CONSOLIDATE
```
# Tests → tests/ directory
test_stage1.py, test_stage2.py, test_stage3.py → tests/test_stages.py
test_api.py → tests/test_api.py
test_*_integration.py → tests/test_data_collection.py

# Documentation → docs/ or README.md
Feature docs → docs/
Architecture decisions → docs/ARCHITECTURE.md
```

### ❌ DELETE
```
# Duplicates
view_db_data.py
view_collected_data.py
view_scraped_content.py
view_scraped_data.py
view_full_data.py
review_collected_data.py
review_database_data.py

# One-time scripts (already executed)
fix_confidence_scores.py

# Temporary/Generated files
data_review_*.json
database_review.json
scraped_companies.json
lob_verifications.csv (add to .gitignore, can regenerate)
*.jpeg, *.jpg
Untitled.rtf

# Outdated documentation
PROJECT_PLAN.md (outdated)
TASKS.md (outdated)
TECH_STACK.md (merge into README)
CONFIDENCE_SCORE_FIX.md (historical)
STAGE_*_COMPLETE.md (historical)
```

---

## Expected Results

### Before Refactoring
- ~100+ files in root directory
- Scattered test files
- Duplicate utility scripts
- Fragmented documentation
- Temporary files not ignored

### After Refactoring
- ~50-60 essential files
- Organized tests/ directory
- Single consolidated utility script
- Streamlined documentation
- Clean project structure
- .gitignore updated

---

## Risk Mitigation

1. **Backup First**: Archive files before deletion
2. **Test After Each Phase**: Verify no regressions
3. **Keep Core Functionality**: Don't remove anything from app/ directory
4. **Preserve Data**: Don't delete data/ directory files
5. **Document Changes**: Update README with new structure

---

## Verification Checklist

- [ ] All tests pass
- [ ] API endpoints work
- [ ] Frontend works
- [ ] Data collection works
- [ ] AI analysis works
- [ ] Database operations work
- [ ] Documentation is up to date
- [ ] No duplicate functionality
- [ ] .gitignore excludes temporary files

---

**Status**: Ready to Execute  
**Estimated Time**: 1-2 hours  
**Risk Level**: Low (mostly file cleanup)

