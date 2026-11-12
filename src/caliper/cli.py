from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from caliper import __version__

app = typer.Typer(add_completion=False, help="Caliper: evidence-gated coding-agent harness")
console = Console()


def _find_docker() -> str | None:
    found = shutil.which("docker")
    if found:
        return found
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "DockerDesktop" / "resources" / "bin" / "docker.exe",
        Path("C:/Program Files/Docker/Docker/resources/bin/docker.exe"),
    ]
    for cand in candidates:
        if cand.exists():
            return str(cand)
    return None


def _read_env(path: Path = Path(".env")) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def _stub(name: str, day: str) -> None:
    console.print(f"[yellow]{name}[/] 尚未实现（计划 {day}）")
    raise typer.Exit(code=2)


@app.command()
def version() -> None:
    """打印版本。"""
    console.print(f"caliper {__version__}")


@app.command()
def demo(steps: int = 6) -> None:
    """离线演示：不调用任何模型。"""
    for i in range(1, steps + 1):
        console.print(f"  step {i} OK  fake-tool | 0 tokens")
    console.print("[green]demo ok[/]：6 步、0 API 调用")


@app.command()
def doctor() -> None:
    """环境体检：Python / venv / mcp / docker / .env。"""
    rows: list[tuple[str, str, str]] = []
    rows.append(("python", sys.version.split()[0], "ok"))
    venv = Path(sys.prefix)
    rows.append(("venv", str(venv), "ok" if (venv / "pyvenv.cfg").exists() else "warn"))
    try:
        import importlib.metadata as md

        rows.append(("mcp", md.version("mcp"), "ok"))
    except Exception as exc:  # noqa: BLE001
        rows.append(("mcp", type(exc).__name__, "missing"))
    docker = _find_docker()
    rows.append(("docker", docker or "-", "ok" if docker else "missing"))
    env = Path(".env")
    rows.append((".env", str(env.resolve()) if env.exists() else "-", "ok" if env.exists() else "missing"))
    values = _read_env(env)
    key = values.get("OPENAI_API_KEY", "")
    rows.append(("api key", "set" if key else "missing", "ok" if key else "missing"))
    rows.append(("model", values.get("CALIPER_MODEL", "-"), "ok" if values.get("CALIPER_MODEL") else "warn"))
    table = Table(title="caliper doctor")
    table.add_column("item")
    table.add_column("value")
    table.add_column("status")
    for r in rows:
        table.add_row(*r)
    console.print(table)


@app.command()
def run(task: str) -> None:
    """执行一个任务（D1 起）。"""
    _stub("run", "D1")


@app.command()
def resume(run_id: str) -> None:
    """从最后一个 committed 检查点恢复（D4）。"""
    _stub("resume", "D4")


@app.command()
def pending() -> None:
    """列出待审批项（D5）。"""
    _stub("pending", "D5")


@app.command()
def approve(approval_id: str) -> None:
    """通过一条审批（D5）。"""
    _stub("approve", "D5")


@app.command()
def deny(approval_id: str, reason: str = "") -> None:
    """拒绝一条审批（D5）。"""
    _stub("deny", "D5")


@app.command()
def trace(run_id: str) -> None:
    """按事件回放一条轨迹（D1）。"""
    _stub("trace", "D1")


@app.command()
def cost(run_id: str | None = None) -> None:
    """token / 成本台账（D1）。"""
    _stub("cost", "D1")


@app.command()
def tasks(action: str = "lint") -> None:
    """任务集管理：lint（D8）。"""
    _stub("tasks", "D8")


@app.command()
def gate(action: str = "run") -> None:
    """评测闸门：run / report / apply（D8–D10）。"""
    _stub("gate", "D8")


@app.command()
def plugin(action: str = "list") -> None:
    """插件管理：new / list（D6）。"""
    _stub("plugin", "D6")


@app.command()
def export(out: str = "web/public/data") -> None:
    """导出只读 JSON 给薄前端（D22）。"""
    _stub("export", "D22")


def main() -> None:
    # Windows CI 默认 cp1252 控制台会让中文输出抛 UnicodeEncodeError
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            pass
    app()


if __name__ == "__main__":
    main()
