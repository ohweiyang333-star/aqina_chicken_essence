"""Run Aqina inbox export and ads performance report as one weekly command."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.scripts.analyze_ads_inbox_performance import (
    build_report,
    default_output_path,
    latest_matching_file,
    load_json,
    summarize_inbox_conversion,
    DEFAULT_ADS_DIR,
)
from backend.scripts.export_marketing_inbox import (
    DEFAULT_GCLOUD_ACCOUNT,
    DEFAULT_PROJECT,
    resolve_output_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Aqina weekly conversion report.")
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--gcloud-account", default=DEFAULT_GCLOUD_ACCOUNT)
    parser.add_argument("--ads-dir", type=Path, default=DEFAULT_ADS_DIR)
    parser.add_argument("--campaigns", type=Path)
    parser.add_argument("--adsets", type=Path)
    parser.add_argument("--ads", type=Path)
    parser.add_argument("--channel", default="all", choices=["all", "messenger", "whatsapp"])
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--inbox-out", type=Path)
    parser.add_argument("--report-out", type=Path, default=default_output_path())
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    inbox_out = resolve_output_path(str(args.inbox_out) if args.inbox_out else None)
    export_command = [
        sys.executable,
        str(Path(__file__).with_name("export_marketing_inbox.py")),
        "--project",
        args.project,
        "--gcloud-account",
        args.gcloud_account,
        "--channel",
        args.channel,
        "--limit",
        str(args.limit),
        "--out",
        str(inbox_out),
    ]
    completed = subprocess.run(export_command, check=True, text=True, capture_output=True)
    export_payload = json.loads(completed.stdout.strip().splitlines()[-1])
    inbox_path = Path(export_payload["output"])

    campaigns_path = args.campaigns or latest_matching_file(args.ads_dir, "campaigns-*.csv")
    adsets_path = args.adsets or latest_matching_file(args.ads_dir, "adsets-*.csv")
    ads_path = args.ads or latest_matching_file(args.ads_dir, "ads-*.csv")
    missing = [
        name
        for name, path in {"campaigns": campaigns_path, "adsets": adsets_path, "ads": ads_path}.items()
        if path is None or not Path(path).exists()
    ]
    if missing:
        raise SystemExit(f"Missing required Ads Manager CSV exports: {', '.join(missing)}")

    report = build_report(
        campaigns_path=Path(campaigns_path),
        adsets_path=Path(adsets_path),
        ads_path=Path(ads_path),
        inbox_path=inbox_path,
    )
    args.report_out.parent.mkdir(parents=True, exist_ok=True)
    args.report_out.write_text(report, encoding="utf-8")
    conversion = summarize_inbox_conversion(load_json(inbox_path))
    print(
        json.dumps(
            {
                "inbox_export": str(inbox_path),
                "report": str(args.report_out),
                "stats": conversion,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
