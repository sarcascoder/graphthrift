"""GraphThrift CLI."""
from __future__ import annotations

import asyncio
import json as jsonlib

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from graphthrift import __version__
from graphthrift.runner import run_demo

app = typer.Typer(add_completion=False, help="GraphThrift — safely shrink LLM cost & latency of KG ingestion.")
console = Console()


def _fmt_pct(x: float) -> str:
    return f"[green]-{x}%[/green]" if x > 0 else f"[red]{x}%[/red]"


def _render(report: dict) -> None:
    b, c = report["baseline"], report["candidate"]
    s, g = report["savings"], report["gate"]
    t = Table(title=f"GraphThrift — {report['candidate_label']} vs baseline ({report['n_episodes']} episodes)")
    for col, right in (("Metric", False), ("Baseline", True), ("Optimized", True), ("Δ", True)):
        t.add_column(col, justify="right" if right else "left")
    t.add_row("Cost (USD)", f"${b['trace']['total_cost_usd']:.5f}", f"${c['trace']['total_cost_usd']:.5f}", _fmt_pct(s["cost_reduction_pct"]))
    t.add_row("LLM calls", str(b["trace"]["total_llm_calls"]), str(c["trace"]["total_llm_calls"]), _fmt_pct(s["llm_calls_reduction_pct"]))
    t.add_row("Latency (ms, summed)", f"{b['trace']['total_latency_ms']:.0f}", f"{c['trace']['total_latency_ms']:.0f}", _fmt_pct(s["latency_reduction_pct"]))
    t.add_row("Prompt tokens", f"{b['trace']['prompt_tokens']:,}", f"{c['trace']['prompt_tokens']:,}", "")
    t.add_row("Entity F1", f"{b['eval']['entity']['f1']}", f"{c['eval']['entity']['f1']}", f"{g['entity_f1_delta']:+.3f}")
    t.add_row("Triple F1", f"{b['eval']['triple']['f1']}", f"{c['eval']['triple']['f1']}", f"{g['triple_f1_delta']:+.3f}")
    console.print(t)
    console.print(f"Calls eliminated: [cyan]{s['calls_eliminated']}[/cyan]  cache hits: [cyan]{s['cache_hits']}[/cyan]  routed: [cyan]{s['routed_calls']}[/cyan]")
    console.print(f"Projected monthly savings @ {s['monthly_volume_episodes']:,} episodes: [bold green]${s['projected_monthly_saved_usd']:,}[/bold green]")
    color = "green" if g["passed"] else "red"
    verdict = report["verdict"]
    console.print(Panel(f"[bold {color}]{'GATE PASS' if g['passed'] else 'GATE FAIL'}[/bold {color}] — {verdict}\n" + "\n".join(g["reasons"]),
                        title="Quality gate", border_style=color))


@app.command()
def demo(
    scenario: str = typer.Option("safe", help="safe | aggressive"),
    volume: int = typer.Option(1_000_000, help="episodes/month for savings projection"),
    json: bool = typer.Option(False, "--json", help="emit raw JSON instead of a table"),
) -> None:
    """Run the offline baseline-vs-optimized demo and print a report."""
    report = asyncio.run(run_demo(scenario, monthly_volume=volume))
    if json:
        console.print_json(jsonlib.dumps(report))
    else:
        _render(report)


@app.command()
def serve(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
    """Start the GraphThrift API server."""
    import uvicorn

    uvicorn.run("graphthrift.api.app:app", host=host, port=port, reload=reload)


@app.command()
def version() -> None:
    """Print the version."""
    console.print(f"graphthrift {__version__}")


if __name__ == "__main__":
    app()
