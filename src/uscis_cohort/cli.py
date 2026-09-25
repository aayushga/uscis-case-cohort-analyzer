"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import sys

from .client import ApiError, UscisClient
from .cohort import build_cohort, mask_receipt
from .config import Settings
from .store import CaseStore


SANDBOX_WITH_HISTORY = (
    "EAC9999103403", "EAC9999103404", "EAC9999103405", "EAC9999103410",
    "EAC9999103411", "EAC9999103416", "EAC9999103419", "LIN9999106498",
    "LIN9999106499", "LIN9999106504", "LIN9999106505", "LIN9999106506",
    "SRC9999102777", "SRC9999102778", "SRC9999102779", "SRC9999102780",
    "SRC9999102781", "SRC9999102782", "SRC9999102783", "SRC9999102784",
    "SRC9999102785", "SRC9999102786", "SRC9999102787", "SRC9999132710",
    "SRC9999132719",
)
SANDBOX_WITHOUT_HISTORY = (
    "EAC9999103400", "EAC9999103402", "EAC9999103406", "EAC9999103407",
    "EAC9999103408", "EAC9999103409", "EAC9999103412", "EAC9999103413",
    "EAC9999103414", "EAC9999103415", "EAC9999103420", "EAC9999103421",
    "EAC9999103424", "EAC9999103425", "EAC9999103426", "EAC9999103428",
    "EAC9999103429", "EAC9999103431", "EAC9999103432", "LIN9999106501",
    "LIN9999106507", "SRC9999132694", "SRC9999132695", "SRC9999132706",
    "SRC9999132707",
)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="uscis-cohort")
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("sandbox-plan", help="Show official sandbox test receipts and checklist")

    check = sub.add_parser("check", help="Fetch and locally store one case")
    check.add_argument("receipt_number")
    check.add_argument("--show-raw", action="store_true")

    plan = sub.add_parser("plan-cohort", help="Preview a sequential receipt cohort offline")
    plan.add_argument("--center", required=True)
    plan.add_argument("--before", type=int, default=50)
    plan.add_argument("--after", type=int, default=50)
    plan.add_argument("--show-receipts", action="store_true")

    scan = sub.add_parser("scan", help="Fetch and store a bounded receipt cohort")
    scan.add_argument("--center", required=True)
    scan.add_argument("--before", type=int, default=50)
    scan.add_argument("--after", type=int, default=50)
    scan.add_argument("--yes", action="store_true", help="Confirm the request count")

    summary = sub.add_parser("summary", help="Aggregate the latest local observations")
    summary.add_argument("--form", default="I-765")
    return root


def _settings() -> Settings:
    try:
        return Settings.from_environment()
    except ValueError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc


def _sandbox_plan() -> None:
    print("Sandbox checklist:")
    print("1. Create a developer account, team, and Team App at developer.uscis.gov.")
    print("2. Enable 'Case Status API - Sandbox' on the Team App.")
    print("3. Export USCIS_CLIENT_ID and USCIS_CLIENT_SECRET locally.")
    print("4. Generate traffic for 5 consecutive days, including 200 and 4xx responses.")
    print("5. Request production access from developersupport@uscis.dhs.gov.")
    print("\nSupported sandbox receipts with history:")
    print(" ".join(SANDBOX_WITH_HISTORY))
    print("\nSupported sandbox receipts without history:")
    print(" ".join(SANDBOX_WITHOUT_HISTORY))


def _check(args: argparse.Namespace) -> None:
    settings = _settings()
    payload = UscisClient(settings).get_case(args.receipt_number)
    store = CaseStore(settings.database_path)
    try:
        store.save(payload)
    finally:
        store.close()
    case = payload["case_status"]
    print(f"{mask_receipt(args.receipt_number)}: {case.get('formType', '?')} — "
          f"{case.get('current_case_status_text_en', 'Unknown')}")
    if args.show_raw:
        print(json.dumps(payload, indent=2))


def _plan(args: argparse.Namespace) -> None:
    receipts = build_cohort(args.center, args.before, args.after)
    print(f"Planned cohort: {len(receipts)} receipts around {mask_receipt(args.center)}")
    if args.show_receipts:
        print("\n".join(receipts))


def _scan(args: argparse.Namespace) -> None:
    settings = _settings()
    receipts = build_cohort(args.center, args.before, args.after)
    if len(receipts) > settings.max_daily_requests:
        raise SystemExit(
            f"Refusing {len(receipts)} requests; configured daily ceiling is "
            f"{settings.max_daily_requests}"
        )
    if not args.yes:
        raise SystemExit(
            f"Planned {len(receipts)} requests around {mask_receipt(args.center)}. "
            "Re-run with --yes to confirm."
        )
    client, store = UscisClient(settings), CaseStore(settings.database_path)
    succeeded = failed = 0
    try:
        for receipt in receipts:
            try:
                payload = client.get_case(receipt)
                store.save(payload)
                succeeded += 1
                print(f"ok    {mask_receipt(receipt)}")
            except ApiError as exc:
                failed += 1
                print(f"error {mask_receipt(receipt)}: {exc}", file=sys.stderr)
    finally:
        store.close()
    print(f"Completed: {succeeded} saved, {failed} errors")


def _summary(args: argparse.Namespace) -> None:
    settings = _settings()
    store = CaseStore(settings.database_path)
    try:
        rows = list(store.summary(args.form))
    finally:
        store.close()
    print(f"Latest status counts for {args.form}:")
    for status, count in rows:
        print(f"{count:>6}  {status}")


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "sandbox-plan":
            _sandbox_plan()
        elif args.command == "check":
            _check(args)
        elif args.command == "plan-cohort":
            _plan(args)
        elif args.command == "scan":
            _scan(args)
        elif args.command == "summary":
            _summary(args)
        return 0
    except (ApiError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

