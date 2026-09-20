import argparse
import json
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="pyopencode",
        description="Ask questions to opencode from Python or the CLI.",
    )
    parser.add_argument("question", nargs="?", help="Question to ask opencode")
    parser.add_argument("-m", "--model", help="Model to use (provider/model)")
    parser.add_argument("-a", "--agent", help="Agent name to use (defined in opencode config)")
    parser.add_argument("--dir", help="Working directory for the opencode session")
    parser.add_argument("-s", "--session", dest="session_id", help="Continue an existing session by ID")
    parser.add_argument("-c", "--continue", dest="continue_last", action="store_true",
                        help="Continue the last session")
    parser.add_argument("-t", "--timeout", type=int, help="Timeout in seconds")
    parser.add_argument("--list-agents", action="store_true", help="List available opencode agents")
    parser.add_argument("--json", action="store_true", help="Print result as JSON")
    args = parser.parse_args(argv)

    from pyopencode import ask, list_agents

    if args.list_agents:
        print(list_agents().rstrip())
        return

    if not args.question:
        parser.error("question is required (or use --list-agents)")

    try:
        result = ask(
            args.question,
            model=args.model,
            agent=args.agent,
            dir=args.dir,
            session_id=args.session_id,
            continue_last=args.continue_last,
            timeout=args.timeout,
        )
    except Exception as e:
        print(f"pyopencode: error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({
            "text": result.text,
            "session_id": result.session_id,
        }, ensure_ascii=False, indent=2))
    else:
        print(result.text)
    return 0


if __name__ == "__main__":
    sys.exit(main())