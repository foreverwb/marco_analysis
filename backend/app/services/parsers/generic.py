from typing import List

from app.services.cleaning import normalize_header_text
from app.services.parsers.base import BaseParser, ParsedTable, Token, group_tokens_by_row


class GenericParser(BaseParser):
    name = "generic"

    def parse(self, header_tokens: List[Token], body_tokens: List[Token]) -> ParsedTable:
        warnings: List[str] = []
        header_rows = group_tokens_by_row(header_tokens)
        if not header_rows:
            return ParsedTable(
                ok=False,
                parser=self.name,
                columns=[],
                rows=[],
                cell_conf=[],
                warnings=["Unable to find header row. Try cropping the table region."],
            )
        header_row = max(header_rows, key=len)
        columns = [normalize_header_text(token.text).replace(" ", "_") for token in header_row]
        boundaries = []
        for idx, token in enumerate(header_row):
            boundaries.append((token.left, token.right))
        sorted_by_left = sorted(zip(columns, boundaries), key=lambda item: item[1][0])
        columns_sorted = [item[0] for item in sorted_by_left]
        bounds_sorted = [item[1] for item in sorted_by_left]
        column_edges = [-10**9]
        for idx in range(1, len(bounds_sorted)):
            prev_right = bounds_sorted[idx - 1][1]
            next_left = bounds_sorted[idx][0]
            column_edges.append((prev_right + next_left) / 2)
        column_edges.append(10**9)
        data_rows = group_tokens_by_row(body_tokens)
        rows = []
        cell_conf = []
        for row in data_rows:
            row_cells = {col: "" for col in columns_sorted}
            row_conf = [-1 for _ in columns_sorted]
            for col_idx in range(len(columns_sorted)):
                tokens_in_col = [
                    token
                    for token in row
                    if column_edges[col_idx] <= token.x_center < column_edges[col_idx + 1]
                ]
                if tokens_in_col:
                    tokens_in_col = sorted(tokens_in_col, key=lambda t: t.left)
                    row_cells[columns_sorted[col_idx]] = " ".join(t.text for t in tokens_in_col)
                    row_conf[col_idx] = int(sum(t.conf for t in tokens_in_col) / len(tokens_in_col))
            if sum(1 for value in row_cells.values() if value) < max(1, int(0.7 * len(columns_sorted))):
                warnings.append("Skipped a row with too few populated cells.")
                continue
            rows.append(row_cells)
            cell_conf.append(row_conf)
        return ParsedTable(
            ok=True,
            parser=self.name,
            columns=columns_sorted,
            rows=rows,
            cell_conf=cell_conf,
            warnings=warnings,
        )
