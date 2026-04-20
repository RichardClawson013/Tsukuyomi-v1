#!/usr/bin/env python3
"""Thin wrapper around the NightShift protocol runner.

Intended for invocation from cron:
    0 3 * * * /usr/local/bin/python /opt/tsukuyomi/scripts/nightshift.py --config ~/.local/share/tsukuyomi/config/corelaw.json
"""
import sys
from tsukuyomi.protocols.nightshift import main_cli

if __name__ == "__main__":
    sys.exit(main_cli())
