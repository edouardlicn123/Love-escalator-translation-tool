import json
import subprocess
from typing import List, Optional

from .client import AskResult, OpenCodeClient, OpenCodeError


def parse_output(lines: List[str]):
    """Parse opencode's `--format json` NDJSON events.

    Returns (text, session_id). Only events with type=="text" and
    part.type=="text" contribute to the answer text.
    """
    text_parts = []
    session_id = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        if session_id is None:
            session_id = evt.get("sessionID")
        part = evt.get("part") or {}
        if evt.get("type") == "text" and part.get("type") == "text":
            text_parts.append(part.get("text", ""))
    return "\n".join(text_parts).strip(), session_id


class SubprocessClient(OpenCodeClient):
    def __init__(self, opencode_bin: str = "opencode"):
        self.opencode_bin = opencode_bin

    def _build_command(
        self,
        question: str,
        model: Optional[str],
        agent: Optional[str],
        dir: Optional[str],
        session_id: Optional[str],
        continue_last: bool,
    ) -> List[str]:
        cmd = [self.opencode_bin, "run", "--format", "json"]
        if model:
            cmd += ["--model", model]
        if agent:
            cmd += ["--agent", agent]
        if session_id:
            cmd += ["--session", session_id]
        if continue_last:
            cmd += ["--continue"]
        cmd.append(question)
        return cmd

    def ask(
        self,
        question: str,
        *,
        model: Optional[str] = None,
        agent: Optional[str] = None,
        dir: Optional[str] = None,
        session_id: Optional[str] = None,
        continue_last: bool = False,
        timeout: Optional[int] = None,
    ) -> AskResult:
        cmd = self._build_command(question, model, agent, dir, session_id, continue_last)
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=dir,  # opencode v2 无 --dir 参数，改用子进程工作目录
        )
        lines = [l for l in proc.stdout.splitlines() if l.strip()]
        error_msg = self._find_error(lines)
        if proc.returncode != 0:
            stderr = proc.stderr.strip()
            detail = error_msg or stderr
            raise OpenCodeError(
                f"opencode run failed (exit {proc.returncode})"
                + (f": {detail}" if detail else "")
            )
        text, sid = parse_output(lines)
        if not text:
            raise OpenCodeError(error_msg or "opencode returned an empty response")
        raw = [json.loads(l) for l in lines]
        return AskResult(text=text, session_id=sid, raw=raw)

    @staticmethod
    def _find_error(lines: List[str]) -> Optional[str]:
        """Extract the first `error` event message from the NDJSON stream."""
        for line in lines:
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                continue
            if evt.get("type") == "error":
                err = evt.get("error") or {}
                msg = err.get("message") or json.dumps(err, ensure_ascii=False)
                return f"opencode error ({err.get('type', 'unknown')}): {msg}"
        return None
