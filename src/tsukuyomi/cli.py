"""CLI entry point — `tsukuyomi start`, `tsukuyomi init`, etc."""
from __future__ import annotations
import argparse
import asyncio
import os
import shutil
import sys
from pathlib import Path

from tsukuyomi import __version__


def cmd_start(args: argparse.Namespace) -> int:
    from tsukuyomi.core.startup import start
    asyncio.run(start(config_path=args.config))
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    data_root = _data_root(args.dir)
    (data_root / "config").mkdir(parents=True, exist_ok=True)
    (data_root / "data" / "logs").mkdir(parents=True, exist_ok=True)
    (data_root / "data" / "audits").mkdir(parents=True, exist_ok=True)
    (data_root / "data" / "proposals").mkdir(parents=True, exist_ok=True)

    target_config = data_root / "config" / "corelaw.json"
    if target_config.exists() and not args.force:
        print(f"{target_config} already exists (use --force to overwrite)", file=sys.stderr)
        return 2

    example = _find_bundled("config/corelaw.example.json")
    if example:
        shutil.copy(example, target_config)
    else:
        target_config.write_text('{"schema_version":1}\n')

    print(f"initialized Tsukuyomi data root at {data_root}")
    print(f"edit config: {target_config}")
    return 0


def cmd_version(_args: argparse.Namespace) -> int:
    print(f"tsukuyomi {__version__}")
    return 0


def cmd_config_validate(args: argparse.Namespace) -> int:
    from tsukuyomi.core.config import load_config
    try:
        load_config(args.config)
    except Exception as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print("OK")
    return 0


def cmd_memory_stats(args: argparse.Namespace) -> int:
    import sqlite3
    from tsukuyomi.core.config import load_config
    cfg = load_config(args.config)
    path = Path(cfg.memory.sqlite_path).expanduser()
    if not path.exists():
        print("(no memory database yet)")
        return 0
    db = sqlite3.connect(str(path))
    for table in ("events", "requests", "audits", "sandbox_runs"):
        try:
            n = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table}: {n}")
        except sqlite3.OperationalError:
            print(f"{table}: (missing)")
    db.close()
    return 0


def cmd_nightshift(args: argparse.Namespace) -> int:
    from tsukuyomi.protocols.nightshift import run_nightshift
    count = asyncio.run(run_nightshift(args.config, args.lookback_hours))
    print(f"generated {count} proposal(s)")
    return 0


def _data_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    xdg = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local/share")
    return Path(xdg) / "tsukuyomi"


def _find_bundled(rel: str) -> Path | None:
    here = Path(__file__).parent.parent.parent
    for candidate in [here / rel, Path(rel), Path("/usr/share/tsukuyomi") / rel]:
        if candidate.exists():
            return candidate
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tsukuyomi")
    parser.add_argument("--version", action="version", version=f"tsukuyomi {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_start = sub.add_parser("start", help="Start the interceptor service")
    p_start.add_argument("--config", type=str, default=None)
    p_start.set_defaults(func=cmd_start)

    p_init = sub.add_parser("init", help="Initialize a Tsukuyomi data directory")
    p_init.add_argument("--dir", type=str, default=None)
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_ver = sub.add_parser("version", help="Print version")
    p_ver.set_defaults(func=cmd_version)

    p_cfg = sub.add_parser("config", help="Config utilities")
    cfg_sub = p_cfg.add_subparsers(dest="cfg_cmd", required=True)
    p_val = cfg_sub.add_parser("validate")
    p_val.add_argument("--config", required=True)
    p_val.set_defaults(func=cmd_config_validate)

    p_mem = sub.add_parser("memory", help="Memory utilities")
    mem_sub = p_mem.add_subparsers(dest="mem_cmd", required=True)
    p_stats = mem_sub.add_parser("stats")
    p_stats.add_argument("--config", required=True)
    p_stats.set_defaults(func=cmd_memory_stats)

    p_ns = sub.add_parser("nightshift", help="Run NightShift batch")
    p_ns.add_argument("--config", required=True)
    p_ns.add_argument("--lookback-hours", type=int, default=24)
    p_ns.set_defaults(func=cmd_nightshift)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
