# Human Translator

**Rule-based English quantifier & NP tagger** — designed for offline use, deterministic labeling, and easy rule extension.

Tags determiners, quantifiers, numbers, adjectives, adverbs, nouns, and verbs with structural labels (`m1`…`m5`, `N`, `V`, `adv`, …) and semantic subtypes (`cardinal`, `ordinal`, `possessive adj`, `possessive pronoun`, …).

---

## Why this project

| Goal | Approach |
|------|----------|
| **Deterministic** | Explicit priority-ordered rules, not a black-box model |
| **Offline** | One Docker image build; runtime needs no network |
| **Extensible** | Drop a rule file under `src/rules/` → auto-registered |
| **Windows-friendly** | GUI dashboard + watch folder for `.txt` → Excel |

---

## Quick start (Windows)

1. Install & start [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Clone / pull this repo
3. Double-click **`windows\start.bat`**
4. Click **Setup** once (builds offline image + smoke test)
5. Drop a `.txt` file into `data/input` → save (auto-watch) or **Process Once**

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
| `src/rules/np/**` | NP rules (auto-discovered) |
| `src/rules/vp/**` | VP rules (auto-discovered) |
| `Book1.xlsx` | Lexical sets |

---

## Extending rules

### 1. Lexicon only

Edit **`Book1.xlsx`** columns. No rebuild.

### 2. New rule code

1. Add a file under `src/rules/np/...` or `src/rules/vp/...` (class inheriting `Rule`)
2. Save — **auto-discovery registers it** (no importer edit)

Default mounts bind **`src/`** into the container → **no Docker rebuild** for rule logic.

Details: **[docs/ADDING_RULES.md](docs/ADDING_RULES.md)**

### 3. When you need rebuild

| Change | Rebuild? |
|--------|----------|
| Rule Python code | **No** |
| `Book1.xlsx` | **No** |
| `requirements.txt` / spaCy / NLTK | **Yes** |
| Dockerfile | **Yes** |

---

## Project layout

```text
human-translator/
├── windows/              # launchers (start, setup, watch, process)
├── scripts/              # PowerShell GUI / automation
├── docs/                 # WINDOWS.md, ADDING_RULES.md
├── docker/
├── src/                  # tagger + rules (auto-discovered)
├── data/input|output/
├── assets/
├── tests/
├── Book1.xlsx
└── Makefile
```

---

## Labels (cheat sheet)

| Label | Typical use |
|-------|-------------|
| `m1` | Determiner / quantifier / NP-substitute possessives |
| `m2` | Adjective |
| `m3` | Genitive `'s` |
| `m4` | Post-nominal number |
| `N` / `V` / `adv` | Noun / verb / adverb |

**Subtypes** on `m1`: `cardinal`, `ordinal`, `possessive adj`, `possessive pronoun`, …

---

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python -m src.main data/input/test.txt
```

---

## License

See `LICENSE`.
