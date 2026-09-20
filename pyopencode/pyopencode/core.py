import subprocess
from typing import Optional

from .client import AskResult, OpenCodeClient, OpenCodeError
from .subprocess_client import SubprocessClient


def get_client(kind: str = "subprocess", **kwargs) -> OpenCodeClient:
    if kind == "subprocess":
        return SubprocessClient(**kwargs)
    if kind == "http":
        from .http_client import HttpClient

        return HttpClient(**kwargs)
    raise ValueError(f"Unknown client kind: {kind!r}")


def ask(question: str, *, client: Optional[OpenCodeClient] = None, **kwargs) -> AskResult:
    if client is None:
        client = SubprocessClient()
    return client.ask(question, **kwargs)


def list_agents(opencode_bin: str = "opencode") -> str:
    proc = subprocess.run(
        [opencode_bin, "agent", "list"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise OpenCodeError(
            f"opencode agent list failed (exit {proc.returncode})"
            + (f": {proc.stderr.strip()}" if proc.stderr.strip() else "")
        )
    return proc.stdout