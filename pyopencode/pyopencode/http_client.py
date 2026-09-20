from typing import Optional

from .client import AskResult, OpenCodeClient


class HttpClient(OpenCodeClient):
    """OpenCode server over HTTP (opencode serve).

    Stub for now; implement once the subprocess path is validated.
    """

    def __init__(self, base_url: str = "http://127.0.0.1:4096", **kwargs):
        self.base_url = base_url.rstrip("/")

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
        raise NotImplementedError(
            "HttpClient is not implemented yet. Use get_client('subprocess')"
        )
