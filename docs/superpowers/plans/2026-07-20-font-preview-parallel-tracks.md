# Font Preview (font-preview) — Parallel Track Decomposition

> **Purpose:** Break the font-preview implementation into **6 independent parallel tracks** with a **serial prerequisite track** that handles shared files. Each track has:
> - One verifiable deliverable (testable artifact)
> - Files to create/modify (explicit list)
> - Files NOT to touch (guardrail list)
> - Dependencies (blocked by, waits for)

**Architecture:** Click CLI + fonttools parser + Jinja2 template + base64 embedding → single-file HTML preview

**Tech Stack:** Python 3.12, fonttools, click, jinja2, pytest

---

## 【SERIAL PREREQUISITE TRACK】Track 0: Shared Infrastructure

**Owner:** 1 person (serializes all track starts)

**Deliverable:** pyproject.toml + package initialization complete; all tracks can proceed

**Files to Create/Modify:**
- Create: `pyproject.toml` (dependencies + entry point: `font-preview = "font_preview.cli:main"`)
- Create: `src/font_preview/__init__.py` (package docstring + `__version__ = "0.1.0"`)

**Files NOT to Touch:**
- `src/font_preview/cli.py` (owned by Track 1)
- `src/font_preview/generator.py` (owned by Track 2)
- `src/font_preview/template.py` (owned by Track 3)
- `src/font_preview/utils.py` (owned by Track 4)
- `templates/preview.html.j2` (owned by Track 3)
- `tests/` (owned by Track 5)
- `README.md`, `docs/USAGE.md` (owned by Track 6)

**Dependencies:**
- None (first, unblocks all others)

**Verification:**
```bash
python -m pip show font-preview  # Package installed
grep "font-preview = " pyproject.toml  # Entry point exists
cat src/font_preview/__init__.py | grep __version__  # Version set
```

---

## 【PARALLEL TRACK 1】Track 1: CLI Module & Argument Parsing

**Owner:** 1 person (independent after Track 0)

**Deliverable:** Click CLI with `--help`, argument parsing, and tests

**Files to Create/Modify:**
- Create: `src/font_preview/cli.py`
  - Implement Click command `main(font_path, output_path)`
  - Arguments: `font_path` (positional), `-o/--output` (optional)
  - Help text and usage examples
- Create: `tests/test_cli.py`
  - Test: `--help` displays usage
  - Test: CLI invokes generator (mocked)
  - Test: argument parsing works

**Files NOT to Touch:**
- `pyproject.toml` (owned by Track 0, already finalized)
- `src/font_preview/__init__.py` (owned by Track 0)
- `src/font_preview/generator.py` (generator module is external; CLI only calls interface)
- `src/font_preview/utils.py` (not used by CLI)
- `templates/` (not used by CLI)

**Dependencies:**
- Blocked by: Track 0 (needs pyproject.toml entry point)
- Waits for: (nothing else)
- Provides: `font_preview.cli.main()` interface

**Verification:**
```bash
PYTHONPATH=src python -m pytest tests/test_cli.py::test_help_outputs -v
PYTHONPATH=src python -m pytest tests/test_cli.py -v  # All CLI tests pass
grep "font_path" src/font_preview/cli.py  # Argument exists
```

---

## 【PARALLEL TRACK 2】Track 2: Font Parsing & Generator

**Owner:** 1 person (independent after Track 0)

**Deliverable:** Font parsing + HTML generation logic (generator module)

**Files to Create/Modify:**
- Create: `src/font_preview/generator.py`
  - Implement `parse_font(font_path: str) -> dict` using fonttools
  - Extract: name, metrics (unitsPerEm, ascender, descender, glyphCount)
  - Implement `generate_preview(font_path: str, output_path: str | None) -> str`
  - Calls `utils.embed_font_base64()` (external)
  - Calls `template.render_template()` (external)
  - Writes HTML to output_path
- Create: `tests/test_generator.py` (extended with font-parsing tests)
  - Test: `parse_font()` extracts metadata
  - Test: `generate_preview()` writes file (mocks utils + template)

**Files NOT to Touch:**
- `src/font_preview/cli.py` (owned by Track 1; generator only provides interface)
- `src/font_preview/utils.py` (owned by Track 4; generator calls interface only)
- `src/font_preview/template.py` (owned by Track 3; generator calls interface only)
- `templates/` (owned by Track 3)
- `tests/test_cli.py` (owned by Track 1)

**Dependencies:**
- Blocked by: Track 0 (needs pyproject.toml)
- Waits for: (nothing else; mocks external calls)
- Provides: `font_preview.generator.generate_preview()` interface

**Verification:**
```bash
PYTHONPATH=src python -m pytest tests/test_generator.py::test_parse_font -v
PYTHONPATH=src python -m pytest tests/test_generator.py -v  # All generator tests pass
grep "def generate_preview" src/font_preview/generator.py
```

---

## 【PARALLEL TRACK 3】Track 3: Template & HTML Rendering

**Owner:** 1 person (independent after Track 0)

**Deliverable:** HTML template + Jinja2 rendering module

**Files to Create/Modify:**
- Create: `templates/preview.html.j2`
  - Single-file HTML (inlined CSS + JS)
  - Must include: `@font-face`, font name, metrics display, sample text input, color mode toggle
  - Placeholders: `{{ font_name }}`, `{{ metrics }}`, `{{ font_data_uri }}`, `{{ samples }}`
- Create: `src/font_preview/template.py`
  - Implement `render_template(context: dict) -> str`
  - Use Jinja2 Environment + FileSystemLoader
  - Return rendered HTML string
- Create: `tests/test_template.py` (new; optional but recommended)
  - Test: `render_template()` returns HTML string
  - Test: Rendered HTML contains expected placeholders replaced

**Files NOT to Touch:**
- `src/font_preview/generator.py` (owned by Track 2; template provides interface only)
- `src/font_preview/cli.py` (owned by Track 1)
- `src/font_preview/utils.py` (owned by Track 4)
- `tests/test_cli.py`, `tests/test_generator.py` (owned by Tracks 1 & 2)

**Dependencies:**
- Blocked by: Track 0 (needs pyproject.toml with jinja2 dependency)
- Waits for: (nothing else; renders independently)
- Provides: `font_preview.template.render_template()` interface

**Verification:**
```bash
ls -l templates/preview.html.j2  # Template exists
grep "@font-face" templates/preview.html.j2  # Contains @font-face
PYTHONPATH=src python -c "from font_preview.template import render_template; print(render_template.__name__)"
```

---

## 【PARALLEL TRACK 4】Track 4: Utilities (base64 + file naming)

**Owner:** 1 person (independent after Track 0)

**Deliverable:** Base64 embedding + timestamped filename generation

**Files to Create/Modify:**
- Create: `src/font_preview/utils.py`
  - Implement `embed_font_base64(font_path: str) -> str`
    - Read font file, base64 encode, return data URI
  - Implement `timestamped_output_name(font_path: str) -> str`
    - Generate filename with timestamp (YYYYMMDDTHHMMSSZ.html format)
- Extend: `tests/test_generator.py` (or create `tests/test_utils.py`)
  - Test: `embed_font_base64()` returns data: URI
  - Test: `timestamped_output_name()` includes .html and timestamp

**Files NOT to Touch:**
- `src/font_preview/generator.py` (owned by Track 2; utils provides interface only)
- `src/font_preview/cli.py` (owned by Track 1)
- `src/font_preview/template.py` (owned by Track 3)
- `tests/test_cli.py` (owned by Track 1)

**Dependencies:**
- Blocked by: Track 0 (needs pyproject.toml)
- Waits for: (nothing else)
- Provides: `font_preview.utils.embed_font_base64()`, `font_preview.utils.timestamped_output_name()` interfaces

**Verification:**
```bash
PYTHONPATH=src python -m pytest tests/test_generator.py::test_embed_font_base64 -v
PYTHONPATH=src python -c "from font_preview.utils import embed_font_base64, timestamped_output_name; print('OK')"
```

---

## 【PARALLEL TRACK 5】Track 5: Test Suite & Integration

**Owner:** 1 person (can run in parallel with Tracks 1-4, finalizes after all others)

**Deliverable:** Complete test coverage + integration tests

**Files to Create/Modify:**
- Extend: `tests/test_cli.py` (from Track 1)
  - Add integration test: CLI → generator → HTML output
- Extend: `tests/test_generator.py` (from Track 2)
  - Add mock FakeTTFont for font parsing tests
- Create: `tests/conftest.py` (pytest fixtures, optional)
  - Fixtures for temp fonts, mock fonttools, etc.
- Create: `tests/test_integration.py` (optional but recommended)
  - Full end-to-end: CLI invocation → HTML file → verify contents

**Files NOT to Touch:**
- `src/font_preview/` (all modules finalized by other tracks)
- `templates/` (owned by Track 3)

**Dependencies:**
- Waits for: Track 1 (needs CLI module), Track 2 (needs generator), Track 3 (needs template), Track 4 (needs utils)
- Blocks: None (final validation only)

**Verification:**
```bash
PYTHONPATH=src python -m pytest tests/ -v  # All tests pass
PYTHONPATH=src python -m pytest tests/ --cov=font_preview  # Coverage report
```

---

## 【PARALLEL TRACK 6】Track 6: Documentation

**Owner:** 1 person (independent; no code dependencies)

**Deliverable:** README + USAGE guide

**Files to Create/Modify:**
- Modify: `README.md`
  - Add: Installation section (`pip install -e .`)
  - Add: Quick start example (`font-preview font.ttf -o out.html`)
  - Add: Project description (1-2 sentences)
- Create: `docs/USAGE.md`
  - Command syntax and flags documentation
  - Usage examples (5-6 scenarios)
  - Features list
  - Limitations and notes (CJK file size, single-file constraint)
  - Troubleshooting guide

**Files NOT to Touch:**
- `src/` (all code modules)
- `templates/` (owned by Track 3)
- `tests/` (owned by Track 5)
- `pyproject.toml` (owned by Track 0)

**Dependencies:**
- Blocked by: None (can start immediately after Track 0 if needed, or run in parallel)
- Provides: User documentation

**Verification:**
```bash
ls -l README.md docs/USAGE.md  # Files exist
grep -q "pip install" README.md  # README has install
grep -q "font-preview" docs/USAGE.md  # USAGE has examples
```

---

## Execution Strategy

**Phase 1: Serial (Track 0 only)**
- 1 person creates pyproject.toml + __init__.py
- Commit, tag, confirm all tasks can now proceed

**Phase 2: Parallel (Tracks 1-6)**
- Tracks 1-4: Implement independent modules (4 people, ~30 min each)
- Track 5: (Can start once modules are available) Run tests (~15 min)
- Track 6: Write docs (1 person, can run fully in parallel, ~20 min)

**Phase 3: Integration & Verification**
- All tracks submit PRs after individual verification
- Merge Track 0 first if not merged
- Merge Tracks 1-4 in any order (no conflicts)
- Merge Track 5 (test updates)
- Merge Track 6 (docs)
- Final: Run full test suite across merged code

---

## Shared Files Summary

**Only ONE track owns each file; others reference via public interfaces:**

| File | Owner Track | Used By | Type |
|------|------------|---------|------|
| `pyproject.toml` | 0 | all | Config (serializes) |
| `src/font_preview/__init__.py` | 0 | all | Package init |
| `src/font_preview/cli.py` | 1 | integration tests | CLI interface |
| `src/font_preview/generator.py` | 2 | Track 5 tests | Generator interface |
| `src/font_preview/template.py` | 3 | Track 2 (calls render_template) | Template rendering |
| `src/font_preview/utils.py` | 4 | Track 2 (calls embed_font_base64, timestamped_output_name) | Utilities |
| `templates/preview.html.j2` | 3 | Track 3 render | HTML template |
| `tests/test_cli.py` | 1 | Track 5 (extends) | CLI tests |
| `tests/test_generator.py` | 2 | Track 5 (extends) | Generator tests |
| `README.md` | 6 | none | User doc |
| `docs/USAGE.md` | 6 | none | User doc |

---

## Dependency Graph

```
Track 0 (pyproject.toml + __init__.py)
    ↓
    ├─→ Track 1 (CLI) ──┐
    ├─→ Track 2 (Generator) ──┐
    ├─→ Track 3 (Template) ──┐
    ├─→ Track 4 (Utils) ──┐
    │                       ├─→ Track 5 (Tests) → Final verification
    └─→ Track 6 (Docs) ────┘
```

---

## Checklist: Before Assigning Parallel Tracks

- [ ] Track 0 complete (pyproject.toml + __init__.py committed)
- [ ] All track owners confirm they understand their file list (what to create, what NOT to touch)
- [ ] Each track owner has clear interfaces (input = what other tracks provide; output = what other tracks consume)
- [ ] Test fixtures/mocks agreed upon (e.g., FakeTTFont for generator tests)
- [ ] Merge strategy confirmed (Track 0 first, then 1-4, then 5, then 6)
