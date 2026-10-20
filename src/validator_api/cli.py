"""CLI validator-api."""
from __future__ import annotations

import argparse
import subprocess
import sys

from validator_api.config import PrReviewConfig, load_env_file
from validator_api.doctor import run_doctor
from validator_api.http_server import serve_http
from validator_api.poller import run_poller
from validator_api.runner import run_validation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="validator-api", description="Runner e webhook do api-validator")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("serve", help="Sobe HTTP webhook + worker")

    run_p = sub.add_parser("run", help="Valida uma PR")
    run_p.add_argument("--pr", type=int, required=True)
    run_p.add_argument("--force", action="store_true")

    sub.add_parser("doctor", help="Verifica ambiente")

    poll_p = sub.add_parser("poll", help="Lista PRs com SHA novo (requer gh)")
    poll_p.add_argument("--run", action="store_true")
    poll_p.add_argument("--pr", type=int, default=0)

    args = parser.parse_args(argv)
    load_env_file()

    if args.command == "serve":
        cfg = PrReviewConfig.from_env()
        if not cfg.repository:
            print("Defina GITHUB_REPOSITORY=org/repo", file=sys.stderr)
            return 1
        return serve_http(cfg)

    if args.command == "run":
        try:
            cfg = PrReviewConfig.from_env()
            return run_validation(cfg, args.pr, force=args.force)
        except subprocess.CalledProcessError as e:
            print(f"Comando falhou: {e}", file=sys.stderr)
            return e.returncode or 1
        except RuntimeError as e:
            print(str(e), file=sys.stderr)
            return 1

    if args.command == "doctor":
        return run_doctor()

    if args.command == "poll":
        poll_argv: list[str] = []
        if args.run:
            poll_argv.append("--run")
        if args.pr:
            poll_argv.extend(["--pr", str(args.pr)])
        return run_poller(poll_argv)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
