#!/usr/bin/env python3
"""
Generate a Bridge Holdings HTML block from an .xlsx file.

INPUT FORMAT (Excel):
  - Row 1 (first row): Title (first non-empty cell in the row is used)
  - Row 2: Column headings (2 or 3 columns supported; more will be included but CSS targets up to first two for nowrap)
  - Rows 3..N: Data rows

USAGE:
  python xlsx_to_bridge_html.py path/to/input.xlsx > output.html
  # or write directly to a file:
  python xlsx_to_bridge_html.py path/to/input.xlsx --out block.html

NOTES:
  * The generated HTML is a self-contained block (no <html> wrapper) suitable for embedding.
  * The title uses Tahoma (with sensible sans fallbacks) and is left-aligned with the table.
  * The first two columns are auto-equalized in width when present; if the table has only
    two columns, only the FIRST column gets the no-wrap styling (per requirements).
"""

from __future__ import annotations
import argparse
import sys
import pandas as pd
from html import escape as html_escape


def _first_non_empty(values) -> str:
    for v in values:
        if pd.notna(v):
            s = str(v).strip()
            if s:
                return s
    return "Untitled"


def _detect_last_used_col(df: pd.DataFrame) -> int:
    """Return 0-based index of the last column that has any non-empty cell from row 2 onward.
    Falls back to the last non-empty col in header row if necessary.
    Raises if nothing is found.
    """
    if df.shape[0] < 2:
        raise ValueError("Excel must have at least two rows (title + headers).")

    # Any non-empty values from row index 1 (second row) downward
    non_empty_any = df.iloc[1:].apply(lambda col: col.notna().any(), axis=0)
    indices = [i for i, has_any in enumerate(non_empty_any) if has_any]

    if not indices:
        # Fallback: look at header row (row 2)
        header_non_empty = [i for i, v in enumerate(df.iloc[1].tolist()) if pd.notna(v) and str(v).strip()]
        if not header_non_empty:
            raise ValueError("No header cells found in row 2.")
        return max(header_non_empty)

    return max(indices)


def _format_cell(v) -> str:
    # Render numbers cleanly (e.g., 3.0 -> 3)
    try:
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
    except Exception:
        pass
    return str(v)


def xlsx_to_html(xlsx_path: str) -> str:
    # Read with header=None so we can control rows precisely
    df = pd.read_excel(xlsx_path, header=None, engine="openpyxl")
    if df.empty:
        raise ValueError("Excel file appears to be empty.")

    # Title = first non-empty cell from row 1
    title = _first_non_empty(df.iloc[0].tolist())

    # Determine used columns and extract headers
    last_col = _detect_last_used_col(df)
    headers = ["" if pd.isna(x) else str(x) for x in df.iloc[1, : last_col + 1].tolist()]
    ncols = len(headers)

    # Data rows (rows 3..N)
    body_df = df.iloc[2:, : last_col + 1].fillna("")
    rows = body_df.values.tolist()

    # Build dynamic CSS for nowrap depending on column count
    if ncols >= 3:
        nowrap_css = (
            ".bridge-holdings th:nth-child(1),\n"
            "    .bridge-holdings th:nth-child(2),\n"
            "    .bridge-holdings td:nth-child(1),\n"
            "    .bridge-holdings td:nth-child(2) { white-space: nowrap; }"
        )
    else:
        nowrap_css = (
            ".bridge-holdings th:nth-child(1),\n"
            "    .bridge-holdings td:nth-child(1) { white-space: nowrap; }"
        )

    # Generate <colgroup>
    colgroup = "\n".join(["        <col />" for _ in range(ncols)])

    # Generate thead
    thead_cells = "".join(f"<th>{html_escape(h)}</th>" for h in headers)
    thead_html = f"""
      <thead>
        <tr>{thead_cells}</tr>
      </thead>"""

    # Generate tbody
    tbody_rows = []
    for r in rows:
        tds = "".join(f"<td>{html_escape(_format_cell(v))}</td>" for v in r)
        tbody_rows.append(f"        <tr>{tds}</tr>")
    tbody_html = "\n".join(tbody_rows) if tbody_rows else "        <!-- No data rows -->"

    # Compose final HTML block
    html = f"""<!-- Auto-generated from {html_escape(xlsx_path)} -->
<div class=\"bridge-holdings\">
  <style>
    /* Center the whole block and shrink-wrap to its content */
    .bridge-holdings {{ width: fit-content; margin: 16px auto; }}

    /* Title sits above the table and is left-aligned within the shrink-wrapped block */
    .bridge-holdings .bh-title {{ 
      margin: 0 0 8px 0; 
      font-family: Tahoma, Verdana, Segoe UI, Arial, sans-serif; /* sans fallbacks */
      font-weight: 700;                   /* try 600 if 700 feels too bold */
      font-size: 1.2rem;                  /* slightly larger than body */
      letter-spacing: 0.2px;              /* subtle polish; remove if undesired */
      line-height: 1.2; 
    }}

    /* Table styles */
    .bridge-holdings table.bridge-holdings {{ 
      border-collapse: collapse; 
      width: fit-content;            /* shrink-wrap to content */
      margin: 0;                     /* title handles spacing */
      background: transparent;
      table-layout: auto;            /* allow natural content sizing */
    }}
    .bridge-holdings th, .bridge-holdings td {{ 
      border: 1px solid #000; 
      padding: 6px 10px; 
      background: transparent; 
    }}
    .bridge-holdings thead th {{ text-align: left; white-space: nowrap; }}

    /* Conditional nowrap for columns (depends on # of columns in the sheet) */
    {nowrap_css}

    /* Right-align the last column (numbers) */
    .bridge-holdings th:last-child, 
    .bridge-holdings td:last-child {{ text-align: right; padding-right: 12px; }}

    .bridge-holdings .red {{ color: rgb(192, 22, 22); }}
  </style>

  <div class=\"bh-wrap\">
    <h3 class=\"bh-title\">{html_escape(title)}</h3>

    <table class=\"bridge-holdings\">
      <colgroup>
{colgroup}
      </colgroup>
{thead_html}
      <tbody>
{tbody_html}
      </tbody>
    </table>
  </div>

  <script>
    (function () {{
      /** Equalize the widths of the first two columns to the larger of the two, per table. */
      function equalizeFirstTwoColumns(table) {{
        const cols = table.querySelectorAll('colgroup col');
        if (!cols || cols.length < 2) return;

        // Reset any previous widths before measuring
        cols[0].style.width = 'auto';
        cols[1].style.width = 'auto';

        let maxPx = 0;
        // Measure headers + body cells in the first two columns
        for (const row of table.rows) {{
          for (let i = 0; i < 2; i++) {{
            const cell = row.cells[i];
            if (!cell) continue;
            // Use getBoundingClientRect for accurate rendered width (includes padding + borders)
            const w = cell.getBoundingClientRect().width;
            if (w > maxPx) maxPx = w;
          }}
        }}
        const px = Math.ceil(maxPx) + 'px';
        cols[0].style.width = px;
        cols[1].style.width = px;
      }}

      function equalizeAll() {{
        document.querySelectorAll('table.bridge-holdings').forEach(equalizeFirstTwoColumns);
      }}

      // Initial run
      if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', equalizeAll);
      }} else {{
        equalizeAll();
      }}
      // Re-run when fonts finish loading, on resize, and on load (helps with async layout shifts)
      window.addEventListener('load', equalizeAll);
      window.addEventListener('resize', equalizeAll);

      // Expose a helper so you can call it after dynamically injecting rows
      window.equalizeBridgeHoldingColumns = equalizeAll;
    }})();
  </script>
</div>
"""

    return html


def main():
    p = argparse.ArgumentParser(description="Generate Bridge Holdings HTML from an .xlsx file.")
    p.add_argument("xlsx", help="Path to the input .xlsx file")
    p.add_argument("--out", "-o", help="Write output HTML to this file (defaults to stdout)")
    args = p.parse_args()

    try:
        html = xlsx_to_html(args.xlsx)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(html)
    else:
        sys.stdout.write(html)


if __name__ == "__main__":
    main()
