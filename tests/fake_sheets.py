"""
Google Sheets stand-in for tests.

FakeClient looks like the gspread client from connect_to_sheets(), but keeps
everything in memory:
- The pricing spreadsheet ("real" dataset) serves the fixed snapshot in
  tests/fixtures/sheets/ (one CSV per worksheet, exactly as get_all_values()
  would return it, title rows included). The rows are invented test data.
- Every other spreadsheet (saved orders, proposals, form responses, ...)
  starts empty. The app creates the worksheets it needs, like it would on a
  brand new Google Sheet.

The app uses it when the PBP_FAKE_SHEETS environment variable is set
(see connect_to_sheets in src/data_loader.py). Production never sets it.
"""

import csv
import os

import gspread

from src.data_loader import DATASET_CONFIGS

SNAPSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures', 'sheets')
CATALOG_SHEETS = ['Data', 'Metadata', 'Partner-Specific Info']


class FakeSheet:
    """A tiny in-memory worksheet. Put exceptions in fail['method'] to make the next calls fail."""

    def __init__(self, rows, row_count=1000, title='Sheet1'):
        self.rows = [list(r) for r in rows]
        self.title = title
        self.row_count = row_count  # grid size as cached on the handle, like gspread
        self.grid_rows = row_count  # real grid size on Google's side
        self.fail = {}

    def _maybe_fail(self, method):
        if self.fail.get(method):
            raise self.fail[method].pop(0)

    def get_all_values(self):
        self._maybe_fail('get_all_values')
        return [list(r) for r in self.rows]

    def get_all_records(self):
        headers = self.rows[0] if self.rows else []
        return [dict(zip(headers, r + [''] * (len(headers) - len(r)))) for r in self.rows[1:]]

    def batch_get(self, ranges):  # whole-column ranges like 'A:C'
        self._maybe_fail('batch_get')
        result = []
        for cell_range in ranges:
            first, last = (ord(c) - ord('A') for c in cell_range.split(':'))
            result.append([r[first:last + 1] for r in self.rows])
        return result

    def row_values(self, number):
        return list(self.rows[number - 1]) if number <= len(self.rows) else []

    def append_row(self, row, **kwargs):
        self._maybe_fail('append_row')
        if any(len(str(v)) > 50000 for v in row):
            raise Exception("cell over 50000 characters")
        self.rows.append(list(row))

    def append_rows(self, rows, **kwargs):
        for row in rows:
            self.append_row(row)

    def update_cell(self, row_number, col_number, value):
        self._maybe_fail('update_cell')
        while len(self.rows) < row_number:
            self.rows.append([])
        row = self.rows[row_number - 1]
        row.extend([''] * (col_number - len(row)))
        row[col_number - 1] = value

    def delete_rows(self, start, end=None):
        del self.rows[start - 1:(end or start)]

    def resize(self, rows):
        self.row_count = self.grid_rows = rows

    def update(self, range_name, values):  # e.g. 'C2' or 'G2:H2'
        self._maybe_fail('update')
        first = range_name.split(':')[0]
        col_number = ord(first[0]) - ord('A') + 1
        if int(first[1:]) > self.grid_rows:
            raise Exception("exceeds grid limits")
        for row_offset, row in enumerate(values):
            for offset, value in enumerate(row):
                if len(str(value)) > 50000:
                    raise Exception("cell over 50000 characters")
                self.update_cell(int(first[1:]) + row_offset, col_number + offset, value)

    def batch_update(self, updates):  # [{'range': 'AX2', 'values': [['TRUE']]}, ...], one cell each
        self._maybe_fail('batch_update')
        for item in updates:
            self.update_cell(*gspread.utils.a1_to_rowcol(item['range']), item['values'][0][0])


class FakeSpreadsheet:
    """A spreadsheet: a dict of worksheet name -> FakeSheet."""

    def __init__(self, sheets=None):
        self.sheets = sheets or {}

    def worksheet(self, name):
        if name not in self.sheets:
            raise gspread.exceptions.WorksheetNotFound(name)
        return self.sheets[name]

    def worksheets(self):
        return list(self.sheets.values())

    def add_worksheet(self, title, rows=1000, cols=26):
        self.sheets[title] = FakeSheet([], row_count=rows, title=title)
        return self.sheets[title]


def _read_snapshot(sheet_name):
    with open(os.path.join(SNAPSHOT_DIR, f'{sheet_name}.csv'), newline='', encoding='utf-8') as f:
        return list(csv.reader(f))


class FakeClient:
    """Stands in for the gspread client. Spreadsheets are opened by key or URL."""

    def __init__(self):
        catalog = FakeSpreadsheet({name: FakeSheet(_read_snapshot(name), title=name) for name in CATALOG_SHEETS})
        self.books = {DATASET_CONFIGS['real']['spreadsheet_id']: catalog}

    def open_by_key(self, key):
        return self.books.setdefault(key, FakeSpreadsheet())

    def open_by_url(self, url):
        return self.open_by_key(url.split('/d/')[1].split('/')[0])
