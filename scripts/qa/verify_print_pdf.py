"""Optional local print QA. Requires PyMuPDF in the QA environment, not the app.

python scripts/qa/verify_print_pdf.py dashboard.pdf --expected-runs 105 --expected-usage 126
Synthetic acceptance IDs are run-00000000..run-00000104 (displayed first 12 chars).
Synthetic usage actions are explain-0..explain-125.
"""

import argparse
import json
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--expected-runs", type=int, default=0)
    parser.add_argument("--expected-usage", type=int, default=0)
    args = parser.parse_args()
    if args.expected_runs < 0 or args.expected_usage < 0:
        parser.error("expected row counts must be non-negative")
    try:
        import pymupdf
    except ImportError:
        parser.error("Install PyMuPDF in a separate QA environment")
    with pymupdf.open(args.pdf) as document:
        assert document.page_count > 0
        texts = [page.get_text() for page in document]
        assert all(text.strip() for text in texts), "unexpected blank print page"
        assert all(page.rect.width > page.rect.height for page in document), "expected landscape"
        content = "\n".join(texts)
        assert "Tổng quan" in content and "Run trong snapshot" in content
        assert "Đăng xuất" not in content, "sidebar leaked into print"
        assert "Snapshot hết hạn" in content, "missing retention limitation"
        assert "Asia/" in content, "missing filter timezone"
        if args.expected_runs:
            for index in range(args.expected_runs):
                assert f"run-{index:08d}"[:12] in content, f"missing row {index}"
        if args.expected_usage:
            for index in range(args.expected_usage):
                assert re.search(rf"\bexplain-{index}\b", content), f"missing usage row {index}"
        print(
            json.dumps(
                {
                    "pages": document.page_count,
                    "landscape": True,
                    "expected_rows_present": args.expected_runs,
                    "expected_usage_rows_present": args.expected_usage,
                    "blank_pages": 0,
                }
            )
        )


if __name__ == "__main__":
    main()
