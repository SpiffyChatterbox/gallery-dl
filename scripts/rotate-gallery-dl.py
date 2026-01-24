#!/usr/bin/env python3
"""
rotate-gallery-dl.py - Rotate through URLs with time limits

Runs gallery-dl on each URL for a specified time, then moves to the next.
Uses the archive feature to skip already-downloaded files on subsequent rotations.

Usage:
    rotate-gallery-dl.py [options] <urls_file>

Examples:
    # Basic usage - 1 hour per URL
    ./rotate-gallery-dl.py urls.txt

    # 30 minutes per URL with config file
    ./rotate-gallery-dl.py -t 30m -c /path/to/config.json urls.txt

    # Use development version with logging
    ./rotate-gallery-dl.py --dev --log rotation.log -t 1h urls.txt

    # Verbose gallery-dl output
    ./rotate-gallery-dl.py -v urls.txt
"""

import argparse
import subprocess
import signal
import sys
import time
from datetime import datetime
from pathlib import Path


def parse_time(time_str):
    """Parse time string like '1h', '30m', '90s', '1h30m' into seconds."""
    if time_str.isdigit():
        return int(time_str)

    total = 0
    current = ""

    for char in time_str.lower():
        if char.isdigit():
            current += char
        elif char == 'h':
            total += int(current) * 3600
            current = ""
        elif char == 'm':
            total += int(current) * 60
            current = ""
        elif char == 's':
            total += int(current)
            current = ""

    if current:
        total += int(current)

    return total if total > 0 else 3600  # Default 1 hour


def format_duration(seconds):
    """Format seconds into human-readable duration."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")

    return "".join(parts)


class RotationLogger:
    """Simple logger for rotation events."""

    def __init__(self, log_file=None):
        self.log_file = Path(log_file) if log_file else None
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, message):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}"

        # Always print to console
        print(entry)

        # Optionally write to file
        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(entry + "\n")


def load_urls(urls_file):
    """Load URLs from file, skipping empty lines and comments."""
    path = Path(urls_file)
    if not path.exists():
        raise FileNotFoundError(f"URLs file not found: {urls_file}")

    urls = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            urls.append(line)

    return urls


def build_command(url, args):
    """Build the gallery-dl command."""
    if args.dev:
        cmd = [sys.executable, "-m", "gallery_dl"]
    else:
        cmd = ["gallery-dl"]

    if args.config:
        cmd.extend(["-c", args.config])

    if args.verbose:
        cmd.append("-v")

    # Pass through any extra arguments
    if args.gdl_args:
        cmd.extend(args.gdl_args)

    cmd.append(url)
    return cmd


def run_gallery_dl(url, time_limit_seconds, args, logger):
    """Run gallery-dl on URL for specified time, then gracefully stop."""
    cmd = build_command(url, args)

    logger.log(f"START: {url}")
    logger.log(f"  Command: {' '.join(cmd)}")
    logger.log(f"  Time limit: {format_duration(time_limit_seconds)}")

    start_time = time.time()

    try:
        proc = subprocess.Popen(cmd)

        while proc.poll() is None:
            elapsed = time.time() - start_time
            if elapsed >= time_limit_seconds:
                elapsed_str = format_duration(elapsed)
                logger.log(f"TIMEOUT: {url} (ran for {elapsed_str})")

                # Send SIGINT for graceful shutdown
                proc.send_signal(signal.SIGINT)

                try:
                    proc.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    logger.log(f"  Force killing process...")
                    proc.kill()
                    proc.wait()

                return "timeout", elapsed

            time.sleep(1)

        # Process completed naturally
        elapsed = time.time() - start_time
        elapsed_str = format_duration(elapsed)

        if proc.returncode == 0:
            logger.log(f"COMPLETE: {url} (ran for {elapsed_str})")
            return "completed", elapsed
        else:
            logger.log(f"ERROR: {url} exited with code {proc.returncode} "
                       f"(ran for {elapsed_str})")
            return "error", elapsed

    except Exception as e:
        elapsed = time.time() - start_time
        logger.log(f"EXCEPTION: {url} - {e}")
        return "exception", elapsed


def main():
    parser = argparse.ArgumentParser(
        description="Rotate through URLs with gallery-dl, time-limited per URL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "urls_file",
        help="File containing URLs (one per line, # for comments)"
    )

    parser.add_argument(
        "-t", "--time",
        default="1h",
        help="Time limit per URL (e.g., '1h', '30m', '90s', '1h30m'). "
             "Default: 1h"
    )

    parser.add_argument(
        "-c", "--config",
        help="Path to gallery-dl config file"
    )

    parser.add_argument(
        "--dev",
        action="store_true",
        help="Use development version (python -m gallery_dl) instead of "
             "system install"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Pass -v flag to gallery-dl for verbose output"
    )

    parser.add_argument(
        "-l", "--log",
        help="Log rotation events to file (in addition to console)"
    )

    parser.add_argument(
        "gdl_args",
        nargs="*",
        help="Additional arguments to pass to gallery-dl (after --)"
    )

    # Handle -- separator for pass-through args
    if "--" in sys.argv:
        idx = sys.argv.index("--")
        our_args = sys.argv[1:idx]
        gdl_args = sys.argv[idx + 1:]
    else:
        our_args = sys.argv[1:]
        gdl_args = []

    args = parser.parse_args(our_args)
    args.gdl_args = gdl_args

    # Setup
    time_limit = parse_time(args.time)
    logger = RotationLogger(args.log)
    urls = load_urls(args.urls_file)

    if not urls:
        logger.log("ERROR: No URLs found in file")
        sys.exit(1)

    logger.log(f"INIT: Loaded {len(urls)} URLs, {format_duration(time_limit)} "
               f"per URL")
    logger.log(f"  URLs file: {args.urls_file}")
    logger.log(f"  Mode: {'development' if args.dev else 'system install'}")
    if args.config:
        logger.log(f"  Config: {args.config}")
    if args.log:
        logger.log(f"  Log file: {args.log}")

    rotation = 0

    try:
        while True:
            rotation += 1
            logger.log(f"ROTATION {rotation}: Starting cycle through "
                       f"{len(urls)} URLs")

            for i, url in enumerate(urls, 1):
                logger.log(f"URL {i}/{len(urls)}: {url}")
                status, elapsed = run_gallery_dl(
                    url, time_limit, args, logger)

            logger.log(f"ROTATION {rotation}: Completed full cycle")

    except KeyboardInterrupt:
        logger.log("INTERRUPTED: Received Ctrl+C, shutting down")
        sys.exit(0)


if __name__ == "__main__":
    main()
