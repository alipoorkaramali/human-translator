import sys
import os
import glob
import logging

from src.utils import (
    setup_nltk, read_text_file, save_text_file,
    ensure_dir, get_project_root, setup_logging,
)
from src.core.pipeline import Pipeline


def _process_one(pipe, input_path, output_dir):
    """Process a single text file; return True on success."""
    base = os.path.splitext(os.path.basename(input_path))[0]
    output_excel = os.path.join(output_dir, f"output_{base}.xlsx")
    output_txt = os.path.join(output_dir, f"output_{base}.txt")

    text = read_text_file(input_path)
    df = pipe.run(text, output_file=output_excel)

    # Label/rule audit trail (one pair of files per input)
    output_trace_txt = os.path.join(output_dir, f"output_{base}_trace.txt")
    output_trace_xlsx = os.path.join(output_dir, f"output_{base}_trace.xlsx")
    try:
        pipe.save_trace(
            output_trace_txt,
            path_xlsx=output_trace_xlsx,
            source_name=input_path,
        )
        logging.info("Trace -> %s", output_trace_txt)
    except Exception as exc:
        logging.warning("Trace write failed: %s", exc)

    summary = (
        f"File: {input_path}\n"
        f"Tokens: {len(df)}\n"
        f"Labels:\n{df['برچسب'].value_counts().to_string()}"
    )
    save_text_file(output_txt, summary)

    # Also write legacy names for tooling that expects output.xlsx
    legacy_xlsx = os.path.join(output_dir, "output.xlsx")
    legacy_txt = os.path.join(output_dir, "output.txt")
    try:
        import shutil
        shutil.copy2(output_excel, legacy_xlsx)
        shutil.copy2(output_txt, legacy_txt)
    except Exception:
        pass

    logging.info("OK -> %s", output_excel)
    return True


def main():
    setup_logging(level=logging.INFO)
    root = get_project_root()
    input_dir = os.path.join(root, "data", "input")
    output_dir = os.path.join(root, "data", "output")
    ensure_dir(output_dir)

    if len(sys.argv) >= 2:
        paths = [sys.argv[1]]
    else:
        paths = sorted(
            p for p in glob.glob(os.path.join(input_dir, "*.txt"))
            if not os.path.basename(p).startswith(("~", ".", "_smoke"))
        )
        if not paths:
            logging.error(
                "No input file given and no .txt found in data/input/.\n"
                "Usage:\n"
                "  python -m src.main data/input/mytext.txt\n"
            )
            sys.exit(1)
        logging.info("No CLI args — processing %d file(s) in data/input/", len(paths))

    for p in paths:
        if not os.path.isfile(p):
            logging.error("Input file not found: %s", p)
            sys.exit(1)

    setup_nltk()

    excel_path = os.path.join(root, "Book1.xlsx")
    if not os.path.exists(excel_path):
        logging.error("Book1.xlsx not found at: %s", excel_path)
        sys.exit(1)

    pipe = Pipeline(excel_file=excel_path)
    ok = 0
    for p in paths:
        try:
            if _process_one(pipe, p, output_dir):
                ok += 1
        except Exception as e:
            logging.exception("Failed on %s: %s", p, e)
            sys.exit(1)

    logging.info("Done. %d file(s) processed. Outputs in %s/", ok, output_dir)


if __name__ == "__main__":
    main()
