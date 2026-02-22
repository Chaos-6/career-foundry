/**
 * CSV download utility — generates and triggers download of a CSV file.
 *
 * Handles proper escaping of values containing commas, quotes, or newlines
 * per RFC 4180. Uses Blob + URL.createObjectURL for zero-dependency downloads.
 */

/**
 * Download an array of flat objects as a CSV file.
 *
 * @param rows  Array of objects — each key becomes a column header.
 * @param filename  Name for the downloaded file (include .csv extension).
 * @param columns  Optional ordered list of column keys. If omitted, uses
 *                 Object.keys of the first row.
 */
export function downloadCsv<T extends Record<string, unknown>>(
  rows: T[],
  filename: string,
  columns?: (keyof T)[]
): void {
  if (rows.length === 0) return;

  const cols = columns || (Object.keys(rows[0]) as (keyof T)[]);

  const escapeCell = (value: unknown): string => {
    const str = value == null ? "" : String(value);
    // Wrap in quotes if the value contains a comma, quote, or newline
    if (str.includes(",") || str.includes('"') || str.includes("\n")) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };

  const header = cols.map((c) => escapeCell(String(c))).join(",");
  const body = rows
    .map((row) => cols.map((c) => escapeCell(row[c])).join(","))
    .join("\n");

  const csv = `${header}\n${body}`;
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.style.display = "none";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  // Clean up the object URL after a short delay
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
