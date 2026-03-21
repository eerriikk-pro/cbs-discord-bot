"""Append score rows to Google Sheets (columns A–F)."""

from __future__ import annotations

import os

import gspread


def append_score_row(
    *,
    day: str,
    name: str,
    difficulty: str,
    time: str,
    perfect: str,
    hints: str,
    spreadsheet_id: str | None = None,
    credentials_path: str | None = None,
) -> None:
    """
    Append one row: Day, Name, Difficulty, Time, Perfect?, Hints?
    Uses GOOGLE_APPLICATION_CREDENTIALS (path to service account JSON) if credentials_path is None.
    """
    sid = spreadsheet_id or os.environ.get("SPREADSHEET_ID")
    if not sid:
        raise RuntimeError("SPREADSHEET_ID is not set.")

    creds = credentials_path or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS is not set.")

    gc = gspread.service_account(filename=creds)
    sh = gc.open_by_key(sid)
    ws = sh.sheet1
    row = [day, name, difficulty, time, perfect, hints]
    ws.append_row(row, value_input_option="USER_ENTERED")
