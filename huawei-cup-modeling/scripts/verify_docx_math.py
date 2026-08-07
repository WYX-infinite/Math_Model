#!/usr/bin/env python3
"""Check whether a DOCX contains Word equation objects and obvious raw LaTeX."""

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}

LATEX_COMMAND_RE = re.compile(
    r"\\(?:frac|sum|int|prod|sqrt|alpha|beta|gamma|lambda|mu|sigma|theta|begin|end|left|right)\b"
)


def read_document_xml(docx_path: Path) -> str:
    with zipfile.ZipFile(docx_path) as zf:
        try:
            return zf.read("word/document.xml").decode("utf-8")
        except KeyError as exc:
            raise RuntimeError("word/document.xml not found; file may not be a valid DOCX") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify DOCX math objects.")
    parser.add_argument("docx", help="Path to .docx file")
    parser.add_argument("--min-equations", type=int, default=1, help="Minimum OMML equations expected")
    args = parser.parse_args()

    docx_path = Path(args.docx)
    if not docx_path.exists():
        print(f"ERROR: file not found: {docx_path}", file=sys.stderr)
        return 2

    xml = read_document_xml(docx_path)
    root = ET.fromstring(xml)

    equations = root.findall(".//m:oMath", NS) + root.findall(".//m:oMathPara", NS)
    text_nodes = [node.text or "" for node in root.findall(".//w:t", NS)]
    plain_text = "\n".join(text_nodes)
    latex_hits = sorted(set(LATEX_COMMAND_RE.findall(plain_text)))

    print(f"docx: {docx_path}")
    print(f"omml_equation_nodes: {len(equations)}")
    print(f"raw_latex_command_hits: {', '.join(latex_hits) if latex_hits else 'none'}")

    failed = False
    if len(equations) < args.min_equations:
        print(f"ERROR: expected at least {args.min_equations} Word equation object(s).", file=sys.stderr)
        failed = True
    if latex_hits:
        print("ERROR: raw LaTeX commands appear in normal text nodes.", file=sys.stderr)
        failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
