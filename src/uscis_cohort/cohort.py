"""Receipt-number validation and deterministic cohort construction."""

from __future__ import annotations

import re


RECEIPT_PATTERN = re.compile(r"^(?P<prefix>[A-Z]{3})(?P<number>\d{10})$")


def normalize_receipt(receipt_number: str) -> str:
    value = receipt_number.replace("-", "").replace(" ", "").upper()
    if not RECEIPT_PATTERN.fullmatch(value):
        raise ValueError("Receipt number must contain three letters followed by ten digits")
    return value


def mask_receipt(receipt_number: str) -> str:
    value = normalize_receipt(receipt_number)
    return f"{value[:3]}******{value[-4:]}"


def build_cohort(center: str, before: int, after: int) -> list[str]:
    if before < 0 or after < 0:
        raise ValueError("before and after must be non-negative")
    center = normalize_receipt(center)
    match = RECEIPT_PATTERN.fullmatch(center)
    assert match is not None
    prefix, serial_text = match.group("prefix"), match.group("number")
    serial = int(serial_text)
    low, high = serial - before, serial + after
    if low < 0 or high > 9_999_999_999:
        raise ValueError("Cohort would cross the receipt-number range")
    return [f"{prefix}{number:010d}" for number in range(low, high + 1)]

