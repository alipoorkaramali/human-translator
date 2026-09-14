# Human Translator

**Rule-based English quantifier & NP tagger** — designed for offline use, deterministic labeling, and easy rule extension.

Tags determiners, quantifiers, numbers, adjectives, adverbs, nouns, and verbs with structural labels (`m1`…`m5`, `N`, `V`, `adv`, …) and semantic subtypes (`cardinal`, `ordinal`, `possessive adj`, `possessive pronoun`, …).

---

## Why this project

| Goal | Approach |
|------|----------|
| **Deterministic** | Explicit priority-ordered rules, not a black-box model |
| **Offline** | One Docker image build; runtime needs no network |
| **Extensible** | Add/edit a rule class → mount `src/` → next run uses it |
| **Windows-friendly** | GUI dashboard + watch folder for `.txt` → Excel |

---

## Quick start (Windows)

1. Install & start [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Clone / pull this repo
3. Double-click **`start.bat`** (or `windows\start.bat`)
4. Click **Setup** once (builds offline image + smoke test)
5. Drop a `.txt` file into `data/input` → **Process** or **Watch**

Outputs land in `data/output/output_<name>.xlsx`.

Full Windows guide: **[docs/WINDOWS.md](docs/WINDOWS.md)**

---

## Quick start (CLI / Linux / macOS)

```bash
# Offline image (NLTK + spaCy baked in — needs network only at build time)
docker build -f docker/Dockerfile.offline -t text-processor .

# Run with live code + data mounts
docker run --rm \
  -v "$PWD/data:/app/data" \
  -v "$PWD/Book1.xlsx:/app/Book1.xlsx" \
  -v "$PWD/src:/app/src" \
  text-processor data/input/test.txt
```

Without mounting `src/`, the image uses the code copied at **build** time.

---

## Architecture

```text
text
  → tokenize + seed labels
  → phases: m1 → m2 → m3 → m4 → m5 → special → VP → np_span
  → Excel / text report
```

| Layer | Role |
|-------|------|
| `src/ht_token.py` | Token: word, label, subtype, role, lock, NP spans |
| `src/core/pipeline.py` | Orchestrates phases |
| `src/core/processor.py` | Runs rules by priority until stable |
| `src/rules/np/**` | NP rules (articles, compounds, ordinals, possessives, …) |
| `src/rules/vp/**` | VP rules |
| `Book1.xlsx` | Lexical sets (articles, compounds, ordinals, possessives, …) |

Rules are plain Python classes (`Rule`) with `priority` and `apply(tokens, ctx)`.

---

## Extending rules (yes — you can)

You can **add, remove, or change rules anytime**. Nothing breaks if you follow the pattern.

### 1. Lexicon only (no code)

Edit **`Book1.xlsx`** columns (`compound`, `ordinal`, `possessive`, …).  
Already mounted at runtime → **next process uses the new lists**. No rebuild.

### 2. New / changed rule code

1. Add or edit a file under `src/rules/...`
2. Register it in `src/core/importers/np_importer.py` (or VP importer)
3. Save

With the default Windows/CLI mounts, **`src/` is bind-mounted into the container**.  
→ **No Docker rebuild required** for rule logic changes.

### 3. When you *do* need rebuild (`setup.ps1 -Rebuild`)

| Change | Rebuild? |
|--------|----------|
| Rule Python code | **No** (live `src` mount) |
| `Book1.xlsx` | **No** (live mount) |
| `requirements.txt` / spaCy / NLTK data | **Yes** |
| Base Dockerfile | **Yes** |

---

## Project layout

```text
human-translator/
├── start.bat / setup.bat / watch.bat / process.bat   # shortcuts → windows/
├── windows/              # Windows launchers (start, setup, watch, process)
├── scripts/              # PowerShell: GUI, setup, watch, common
├── docs/WINDOWS.md       # Windows offline guide
├── docker/               # Dockerfile + Dockerfile.offline
├── src/                  # Python tagger (rules, pipeline)
├── data/input|output/    # runtime files
├── assets/               # icon generator
├── tests/
├── Book1.xlsx            # lexicon (root — Docker/CI)
├── requirements.txt
└── Makefile
```

---

## Labels (cheat sheet)

| Label | Typical use |
|-------|-------------|
| `m1` | Determiner / quantifier / NP-substitute possessives |
| `m2` | Adjective |
| `m3` | Genitive `'s` (noun-side) |
| `m4` | Post-nominal number (after N in NP) |
| `N` / `V` / `adv` | Noun / verb / adverb |

**Subtypes** on `m1`: `cardinal`, `ordinal`, `possessive adj`, `possessive pronoun`, …

---

## Development

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
python -m src.main data/input/test.txt
```

Tests: see `tests/` and CI under `.github/workflows/`.

---

## License

See `LICENSE`.
