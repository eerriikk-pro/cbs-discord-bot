"""Parse CluesBySam share messages into fields for the Google Sheet (A–F, excluding Name)."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# --- Canonical sheet strings ---
DIFFICULTIES = ("Easy", "Medium", "Hard", "Tricky", "Evil")
DIFFICULTY_MAP = {d.lower(): d for d in DIFFICULTIES}

YES = "Yes"
NO = "No"

# Grid tiles we accept (squares + circles + common variants)
_GRID_CODEPOINTS = frozenset(
    {
        0x1F7E7,
        0x1F7E8,
        0x1F7E9,
        0x1F7EA,
        0x1F7EB,  # large colored squares
        0x1F7E0,
        0x1F7E1,
        0x1F7E2,
        0x1F7E3,
        0x1F7E4,  # large colored circles (hint-capable)
        0x1F534,
        0x1F535,  # red / blue circle
        0x26AA,
        0x26AB,  # medium white / black circle
        0x1F7E5,
        0x1F7E6,  # large red / blue square (if site ever uses)
    }
)

_GREEN_SQUARE = "\U0001F7E9"

_MONTH_PATTERN = (
    r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
_DATE_RE = re.compile(
    rf"\b{_MONTH_PATTERN}\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:\s*,?\s*(\d{{4}}))?\b",
    re.IGNORECASE,
)
_DIFF_RE = re.compile(
    rf"\(\s*({'|'.join(re.escape(d) for d in DIFFICULTIES)})\s*\)",
    re.IGNORECASE,
)
_LESS_THAN_RE = re.compile(r"less\s+than\s+(\d+)\s+minutes?", re.IGNORECASE)
_CLOCK_RE = re.compile(r"\b(\d{1,2}):(\d{2})\b")


def is_clues_by_sam_attempt(text: str) -> bool:
    return "#CluesBySam" in text


@dataclass(frozen=True)
class ParsedScore:
    """Fields for sheet columns A–F (Name is filled by the bot from Discord)."""

    day: str
    difficulty: str
    time: str
    perfect: str
    hints: str


def parse_clues_by_sam(content: str) -> ParsedScore:
    """
    Parse message body. Raises ValueError with a user-facing message on failure.
    Caller should only call when is_clues_by_sam_attempt is True.
    """
    text = content.strip()
    if not text:
        raise ValueError("Empty message.")

    day = _parse_day(text)
    difficulty = _parse_difficulty(text)
    time_str = _parse_time(text)
    grid = _extract_grid(text)
    if not grid:
        raise ValueError("Couldn’t find a score grid (emoji rows).")

    perfect = YES if _is_perfect(grid) else NO
    hints = YES if _has_hint_circles(grid) else NO

    return ParsedScore(
        day=day,
        difficulty=difficulty,
        time=time_str,
        perfect=perfect,
        hints=hints,
    )


def _parse_day(text: str) -> str:
    m = _DATE_RE.search(text)
    if not m:
        raise ValueError("Couldn’t find a puzzle date (e.g. Mar 21st 2026).")
    month_raw = m.group(1)
    day_num = int(m.group(2))
    month_key = month_raw[:3].lower()
    month_abbrev = {
        "jan": "Jan",
        "feb": "Feb",
        "mar": "Mar",
        "apr": "Apr",
        "may": "May",
        "jun": "Jun",
        "jul": "Jul",
        "aug": "Aug",
        "sep": "Sep",
        "oct": "Oct",
        "nov": "Nov",
        "dec": "Dec",
    }.get(month_key)
    if not month_abbrev:
        raise ValueError("Invalid month in date.")
    return f"{month_abbrev} {day_num}"


def _parse_difficulty(text: str) -> str:
    m = _DIFF_RE.search(text)
    if not m:
        raise ValueError("Couldn’t find difficulty (e.g. (Hard)).")

    raw = m.group(1).strip()
    key = raw.lower()
    if key not in DIFFICULTY_MAP:
        raise ValueError(f"Unknown difficulty: {raw!r}.")
    return DIFFICULTY_MAP[key]


def _parse_time(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    for ln in lines:
        m = _CLOCK_RE.fullmatch(ln)
        if m:
            a, b = int(m.group(1)), m.group(2)
            return f"{a:02d}:{b}"

    for ln in lines:
        if "://" in ln:
            continue
        m = _CLOCK_RE.search(ln)
        if m:
            a, b = int(m.group(1)), m.group(2)
            return f"{a:02d}:{b}"

    lm = _LESS_THAN_RE.search(text)
    if lm:
        return f"< {lm.group(1)}"

    raise ValueError("Couldn’t find a time (MM:SS or “less than N minutes”).")


def _is_grid_char(ch: str) -> bool:
    if len(ch) != 1:
        return False
    return ord(ch) in _GRID_CODEPOINTS


def _normalize_emoji_line(line: str) -> str:
    """Strip variation selectors so 🟩️ (base + VS16) parses like 🟩."""
    return line.strip().replace("\ufe0f", "")


def _is_grid_line(line: str) -> bool:
    s = _normalize_emoji_line(line)
    if not s:
        return False
    return all(_is_grid_char(c) for c in s)


def _extract_grid(text: str) -> list[str] | None:
    lines = text.splitlines()
    best: list[str] = []
    current: list[str] = []
    for line in lines:
        if _is_grid_line(line):
            current.append(_normalize_emoji_line(line))
        else:
            if len(current) > len(best):
                best = current
            current = []
    if len(current) > len(best):
        best = current
    return best if best else None


def _is_hint_circle(ch: str) -> bool:
    if len(ch) != 1:
        return False
    cp = ord(ch)
    if 0x1F7E0 <= cp <= 0x1F7E4:
        return True
    if cp in (0x1F534, 0x1F535, 0x26AA, 0x26AB):
        return True
    name = unicodedata.name(ch, "")
    if "CIRCLE" in name and "SQUARE" not in name:
        return True
    return False


def _has_hint_circles(grid: list[str]) -> bool:
    for row in grid:
        for ch in row:
            if _is_hint_circle(ch):
                return True
    return False


def _is_perfect(grid: list[str]) -> bool:
    for row in grid:
        for ch in row:
            if ch != _GREEN_SQUARE:
                return False
    return True
