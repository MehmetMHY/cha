#!/usr/bin/env python3

"""
convert_cha_to_ch - Convert Cha history files to Ch session format.

Cha format (old):
  - Top-level: chat[], id, version, date{epoch{seconds}}, args{model, platform, ...}, config?
  - chat[]: time (float), user, bot, platform?, model?

Ch format (new):
  - Top-level: timestamp (int), platform (str), model (str), base_url (str), messages[]
  - messages[]: time (int), user, bot, platform (str), model (str)
"""

import argparse
import json
import glob
import sys
import os


def parse_platform_field(raw_platform):
    """
    parse cha's platform field which has multiple formats:
      - None / True / False         -> openai, no override
      - "groq"                      -> groq, no override
      - "ollama|gemma3:1b"          -> platform=ollama, model=gemma3:1b
      - "anthropic|claude-3-..."    -> platform=anthropic, model=claude-3-...
      - "xai|grok-3-fast-beta"      -> platform=xai, model=grok-3-fast-beta
      - "https://url|API_KEY_NAME"  -> platform from url, base_url=url, model unchanged

    returns (platform, model_override, base_url)
      - model_override is None if the model should come from args.model
    """

    if raw_platform is None or isinstance(raw_platform, bool):
        return "openai", None, ""

    if not isinstance(raw_platform, str) or not raw_platform:
        return "openai", None, ""

    if "|" not in raw_platform:
        return raw_platform, None, ""

    left, right = raw_platform.split("|", 1)

    # if left looks like a URL, it's "base_url|API_KEY_NAME"
    if left.startswith("http://") or left.startswith("https://"):
        platform_name = _platform_from_url(left)
        return platform_name, None, left

    # otherwise it's "provider|model"
    return left, right, ""


def _platform_from_url(url):
    # extract a short platform name from an API base URL
    url_lower = url.lower()
    known = {
        "groq": "groq",
        "deepseek": "deepseek",
        "anthropic": "anthropic",
        "openai": "openai",
        "ollama": "ollama",
        "localhost": "ollama",
        "together": "together",
        "mistral": "mistral",
        "cohere": "cohere",
        "xai": "xai",
    }
    for keyword, name in known.items():
        if keyword in url_lower:
            return name
    try:
        from urllib.parse import urlparse

        host = urlparse(url).hostname or ""
        parts = host.replace("api.", "").split(".")
        return parts[0] if parts else url
    except Exception:
        return url


def resolve_platform(args_platform, per_msg_platform=None):
    # get the platform string for a message or session
    if per_msg_platform:
        parsed_plat, _, _ = parse_platform_field(per_msg_platform)
        return parsed_plat
    parsed_plat, _, _ = parse_platform_field(args_platform)
    return parsed_plat


def resolve_model(args_model, args_platform, per_msg_model=None):
    # get the model string, respecting pipe overrides
    if per_msg_model:
        return per_msg_model
    _, model_override, _ = parse_platform_field(args_platform)
    if model_override:
        return model_override
    return args_model or "gpt-4.1"


def resolve_base_url(args_platform):
    # get base_url if the platform field contains one
    _, _, base_url = parse_platform_field(args_platform)
    return base_url


def convert_file(filepath):
    # convert a single cha history file to ch session format
    with open(filepath, "r", encoding="utf-8") as f:
        cha = json.load(f)

    chat = cha.get("chat", [])
    args = cha.get("args", {})
    date = cha.get("date", {})

    args_platform = args.get("platform")
    args_model = args.get("model", "gpt-4.1")

    session_platform = resolve_platform(args_platform)
    session_model = resolve_model(args_model, args_platform)

    epoch = date.get("epoch", {})
    timestamp = int(epoch.get("seconds", 0))

    base_url = resolve_base_url(args_platform)

    messages = []
    for msg in chat:
        msg_platform_raw = msg.get("platform", "")
        msg_model_raw = msg.get("model", "")

        msg_platform = (
            resolve_platform(args_platform, msg_platform_raw)
            if msg_platform_raw
            else session_platform
        )
        msg_model = (
            resolve_model(args_model, args_platform, msg_model_raw)
            if msg_model_raw
            else session_model
        )

        is_system = msg.get("bot", "") == "" and messages == []

        messages.append(
            {
                "time": int(msg.get("time", 0)),
                "user": msg.get("user", ""),
                "bot": msg.get("bot", ""),
                "platform": "" if is_system else msg_platform,
                "model": "" if is_system else msg_model,
            }
        )

    return {
        "timestamp": timestamp,
        "platform": session_platform,
        "model": session_model,
        "base_url": base_url,
        "messages": messages,
    }


def gather_input_files(input_path, prefix):
    # collect cha history files from a file path or directory
    if os.path.isfile(input_path):
        return [input_path]

    if os.path.isdir(input_path):
        pattern = os.path.join(input_path, f"{prefix}*.json")
        files = sorted(glob.glob(pattern))
        if not files:
            print(f"No {prefix}*.json files found in: {input_path}", file=sys.stderr)
        return files

    print(f"Input path not found: {input_path}", file=sys.stderr)
    return []


def build_taken_set(check_dir, output_dir, out_prefix):
    # collect all existing ch_session timestamps from the check dir and output dir
    taken = set()
    for d in (check_dir, output_dir):
        if d and os.path.isdir(d):
            for f in os.listdir(d):
                if f.startswith(out_prefix) and f.endswith(".json"):
                    ts = f[len(out_prefix) : -len(".json")]
                    if ts.isdigit():
                        taken.add(int(ts))
    return taken


def make_output_path(input_filepath, output_dir, in_prefix, out_prefix, taken):
    # generate the output filepath, bumping the epoch in the filename to avoid collisions
    filename = os.path.basename(input_filepath)
    if filename.startswith(in_prefix):
        ts_str = filename[len(in_prefix) : -len(".json")]
        if ts_str.isdigit():
            ts = int(ts_str)
            while ts in taken:
                ts += 1
            taken.add(ts)
            return os.path.join(output_dir, f"{out_prefix}{ts}.json")
        filename = out_prefix + filename[len(in_prefix) :]
    return os.path.join(output_dir, filename)


def build_parser():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(
        prog="convert_cha_to_ch",
        description="Convert Cha history files (cha_hs_*.json) to Ch session format (ch_session_*.json).",
        epilog=(
            "examples:\n"
            "  %(prog)s -i ./cha_chats -o ./ch_chats\n"
            "  %(prog)s -i session.json -o ./out/\n"
            "  %(prog)s -i ./cha_chats              (outputs to ./ch_chats)\n"
            "  %(prog)s                              (uses defaults relative to script location)\n"
            "  %(prog)s -i ./old --in-prefix cha_hs_ --out-prefix ch_session_\n"
            "  %(prog)s -c /path/to/ch/sessions   (check collisions against custom dir)\n"
            "  %(prog)s --dry-run -i ./cha_chats\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-c",
        "--check-dir",
        default=os.path.expanduser("~/.ch/tmp"),
        help="Directory of existing Ch sessions to check for filename collisions (default: ~/.ch/tmp)",
    )
    parser.add_argument(
        "-i",
        "--input",
        default=os.path.join(script_dir, "cha_chats"),
        help="Input file or directory of cha history files (default: ./cha_chats relative to script)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output directory for converted files (default: ./ch_chats relative to script)",
    )
    parser.add_argument(
        "--in-prefix",
        default="cha_hs_",
        help="Filename prefix to match in the input directory (default: cha_hs_)",
    )
    parser.add_argument(
        "--out-prefix",
        default="ch_session_",
        help="Filename prefix for output files (default: ch_session_)",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level for output files (default: 2)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be converted without writing any files",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress per-file output, only show the summary",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show details for each converted file",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = args.output or os.path.join(script_dir, "ch_chats")

    input_files = gather_input_files(args.input, args.in_prefix)
    if not input_files:
        sys.exit(1)

    if not args.dry_run:
        os.makedirs(output_dir, exist_ok=True)

    check_dir = args.check_dir if os.path.isdir(args.check_dir) else None
    taken = build_taken_set(check_dir, output_dir, args.out_prefix)

    if not args.quiet:
        print(f"Found {len(input_files)} file(s) to convert")
        if check_dir:
            print(f"Checking collisions against: {check_dir}")
        if args.dry_run:
            print("(dry run -- no files will be written)")

    converted = 0
    errors = 0

    for filepath in input_files:
        out_path = make_output_path(
            filepath, output_dir, args.in_prefix, args.out_prefix, taken
        )

        if args.dry_run:
            if args.verbose:
                print(f"  {os.path.basename(filepath)} -> {os.path.basename(out_path)}")
            converted += 1
            continue

        try:
            ch_session = convert_file(filepath)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(ch_session, f, indent=args.indent)
            converted += 1
            if args.verbose:
                print(f"  {os.path.basename(filepath)} -> {os.path.basename(out_path)}")
        except Exception as e:
            print(f"  ERROR {os.path.basename(filepath)}: {e}", file=sys.stderr)
            errors += 1

    if not args.quiet:
        print(f"Done: {converted} converted, {errors} errors")
        if not args.dry_run:
            print(f"Output: {output_dir}")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
