# pyopencode

Python toolkit for calling opencode from scripts and CLI.

The agent itself is defined in opencode's own config — pyopencode only passes the
agent name through via `--agent`. Built-in agents: `build` (default), `plan`,
`general`, `explore`, `scout`. Custom agents live in
`~/.config/opencode/agents/*.md` (global) or `.opencode/agents/*.md` (project).

## Install

```bash
pip install -e .
```

## Python API

```python
from pyopencode import ask

result = ask("用中文解释一下闭包")
print(result.text)
print(result.session_id)   # 供多轮连续对话

# 多轮:复用上次的 session_id
r2 = ask("继续上面话题,再举一个例子", session_id=result.session_id)

# 指定智能体 / 模型
ask("帮我查这个代码库", agent="explore", model="anthropic/claude-sonnet-4-20250514")

# 列出 opencode 里可用的智能体
from pyopencode import list_agents
print(list_agents())
```

## CLI

```bash
pyopencode "用中文解释一下闭包"
pyopencode --agent explore "找出所有测试文件"
pyopencode --list-agents
pyopencode --json "返回 JSON"   # 结构化输出 text + session_id
```

## Architecture

- `client.py` — `OpenCodeClient` abstract base + `AskResult` dataclass. The HTTP
  client (`get_client('http')`) is reserved as a future backend; today only the
  subprocess client is implemented.
- `subprocess_client.py` — runs `opencode run --format json`, parses the NDJSON
  event stream.
- `http_client.py` — stub for the `opencode serve` HTTP backend (not implemented).

## Tests

```bash
python -m unittest discover tests
```