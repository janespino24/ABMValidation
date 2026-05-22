#!/usr/bin/env python3
"""Send Telegram status updates for the VIVAMACS synthetic full run.

The script intentionally uses only the Python standard library so it can run
inside the existing project environment without extra dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "synthetic_ground_truth"
DEFAULT_LOG_FILE = PROJECT_ROOT / "logs" / "synthetic_ground_truth_full_run.log"
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env" / "telegram_monitor.env"
CANDIDATES = ["A", "B1", "B3"]
SOBOL_SAMPLE_COUNT = 8192
COST_SHARE_COUNT = 1000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--log-file", type=Path, default=DEFAULT_LOG_FILE)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--interval-seconds", type=int, default=3600)
    parser.add_argument("--once", action="store_true", help="Send one status update and exit.")
    parser.add_argument("--dry-run", action="store_true", help="Print the message without sending it.")
    return parser.parse_args()


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open() as handle:
        line_count = sum(1 for _ in handle)
    return max(0, line_count - 1)


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def tmux_session_alive(name: str) -> bool:
    result = subprocess.run(
        ["tmux", "has-session", "-t", name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def tail_lines(path: Path, count: int = 8) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(errors="replace").splitlines()
    return lines[-count:]


def format_percent(done: int, total: int) -> str:
    if total <= 0:
        return "0.0%"
    return f"{done / total:.1%}"


def build_status_message(output_dir: Path, log_file: Path) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alive = tmux_session_alive("vivamacs_full_run")
    lines = [
        "VIVAMACS synthetic run status",
        f"Time: {now}",
        f"tmux vivamacs_full_run: {'running' if alive else 'not running'}",
        "",
        "Sobol checkpoints:",
    ]

    total_sobol_done = 0
    for candidate in CANDIDATES:
        candidate_dir = output_dir / "sobol" / candidate
        checkpoint = candidate_dir / "sobol_checkpoint.csv"
        done = count_csv_rows(checkpoint)
        total_sobol_done += done
        metadata = read_json(candidate_dir / "metadata.json")
        sample_count = int(metadata.get("sample_count", SOBOL_SAMPLE_COUNT))
        lines.append(f"- {candidate}: {done}/{sample_count} ({format_percent(done, sample_count)})")

    total_sobol = SOBOL_SAMPLE_COUNT * len(CANDIDATES)
    lines.append(f"- total: {total_sobol_done}/{total_sobol} ({format_percent(total_sobol_done, total_sobol)})")

    cost_checkpoint = output_dir / "cost_share" / "candidate_A_cost_share_checkpoint.csv"
    cost_done = count_csv_rows(cost_checkpoint)
    lines.extend(
        [
            "",
            f"Cost share: {cost_done}/{COST_SHARE_COUNT} ({format_percent(cost_done, COST_SHARE_COUNT)})",
            "",
            "Recent log:",
        ]
    )
    recent = tail_lines(log_file, 8)
    lines.extend(recent if recent else ["(log file not found yet)"])
    return "\n".join(lines)


def send_telegram(message: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")

    data = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": "true",
        }
    ).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    request = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        response.read()


def main() -> None:
    args = parse_args()
    load_env_file(args.env_file)

    while True:
        try:
            message = build_status_message(args.output_dir, args.log_file)
            if args.dry_run:
                print(message)
            else:
                send_telegram(message)
                print(f"Sent Telegram update at {datetime.now().isoformat(timespec='seconds')}", flush=True)
        except Exception as exc:  # Keep the monitor alive even if Telegram/network has a transient error.
            print(f"Telegram monitor error at {datetime.now().isoformat(timespec='seconds')}: {exc}", flush=True)

        if args.once:
            break
        time.sleep(args.interval_seconds)


if __name__ == "__main__":
    main()
