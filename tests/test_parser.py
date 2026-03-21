"""Tests for CluesBySam message parsing."""

from __future__ import annotations

import pytest

from cbs_parser import ParsedScore, parse_clues_by_sam

MSG_LONG = """I solved the daily #CluesBySam, Mar 21st 2026 (Hard), in less than 9 minutes
🟨🟩🟩🟩
🟩🟨🟨🟩
🟩🟩🟩🟩
🟩🟩🟩🟩
🟩🟩🟩🟩
https://cluesbysam.com/
"""

MSG_SHORT = """#CluesBySam - Mar 21st 2026 (Hard)
05:26
🟨🟩🟩🟩
🟩🟩🟨🟩
🟩🟩🟩🟩
🟨🟩🟩🟨
🟩🟩🟩🟩
"""

MSG_ORANGE_HINTS = """#CluesBySam - Mar 18th 2026 (Tricky)
04:23
🟠🟩🟠🟩
🟠🟩🟩🟨
🟨🟩🟩🟩
🟩🟩🟩🟩
🟨🟩🟩🟩
"""

MSG_YELLOW_CIRCLE = """I solved the daily #CluesBySam, Mar 17th 2026 (Medium), in less than 7 minutes
🟩🟩🟩🟩
🟩🟡🟩🟩
🟩🟩🟨🟩
🟩🟩🟩🟩
🟩🟩🟩🟩
"""

MSG_ALL_GREEN = """#CluesBySam - Mar 9th 2026 (Easy)
01:10
🟩🟩🟩🟩
🟩🟩🟩🟩
🟩🟩🟩🟩
🟩🟩🟩🟩
🟩🟩🟩🟩
"""


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            MSG_LONG,
            ParsedScore(
                day="Mar 21",
                difficulty="Hard",
                time="< 9",
                perfect="No",
                hints="No",
            ),
        ),
        (
            MSG_SHORT,
            ParsedScore(
                day="Mar 21",
                difficulty="Hard",
                time="05:26",
                perfect="No",
                hints="No",
            ),
        ),
        (
            MSG_ORANGE_HINTS,
            ParsedScore(
                day="Mar 18",
                difficulty="Tricky",
                time="04:23",
                perfect="No",
                hints="Yes",
            ),
        ),
        (
            MSG_YELLOW_CIRCLE,
            ParsedScore(
                day="Mar 17",
                difficulty="Medium",
                time="< 7",
                perfect="No",
                hints="Yes",
            ),
        ),
        (
            MSG_ALL_GREEN,
            ParsedScore(
                day="Mar 9",
                difficulty="Easy",
                time="01:10",
                perfect="Yes",
                hints="No",
            ),
        ),
    ],
)
def test_parse_examples(text: str, expected: ParsedScore) -> None:
    assert parse_clues_by_sam(text) == expected


def test_difficulty_case_insensitive() -> None:
    text = """#CluesBySam - Jan 1st 2026 (hard)
00:01
🟩🟩🟩🟩
🟩🟩🟩🟩
🟩🟩🟩🟩
🟩🟩🟩🟩
🟩🟩🟩🟩
"""
    p = parse_clues_by_sam(text)
    assert p.difficulty == "Hard"


def test_time_single_digit_minutes_padded() -> None:
    text = """#CluesBySam - Jan 1st 2026 (Easy)
1:05
🟩🟩🟩🟩
🟩🟩🟩🟩
🟩🟩🟩🟩
🟩🟩🟩🟩
🟩🟩🟩🟩
"""
    assert parse_clues_by_sam(text).time == "01:05"


def test_parse_errors() -> None:
    with pytest.raises(ValueError, match="date"):
        parse_clues_by_sam("#CluesBySam no date (Easy)\n00:01\n🟩")
    with pytest.raises(ValueError, match="difficulty"):
        parse_clues_by_sam("#CluesBySam Mar 1st 2026\n00:01\n🟩")
    with pytest.raises(ValueError, match="time"):
        parse_clues_by_sam(
            "#CluesBySam Mar 1st 2026 (Easy)\n🟩🟩🟩🟩\n🟩🟩🟩🟩\n🟩🟩🟩🟩\n🟩🟩🟩🟩\n🟩🟩🟩🟩\n"
        )
    with pytest.raises(ValueError, match="grid"):
        parse_clues_by_sam("#CluesBySam Mar 1st 2026 (Easy)\n01:00\nhello")
