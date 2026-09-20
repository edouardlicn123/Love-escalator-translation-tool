from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


class OpenCodeError(Exception):
    pass


@dataclass
class AskResult:
    text: str
    session_id: Optional[str] = None
    raw: List[dict] = field(default_factory=list)


class OpenCodeClient(ABC):
    @abstractmethod
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
        raise NotImplementedError
