import typer
from pathlib import Path
from typing import Optional
from enum import Enum

app = typer.Typer(
    name="cupp",
    help="[bold green]CUPP v2[/bold green] — Advanced Password Wordlist Generator",
    rich_markup_mode="rich",
    no_args_is_help=True,
)

profile_app = typer.Typer(help="Profile management commands")
app.add_typer(profile_app, name="profile")


class Preset(str, Enum):
    fast = "fast"
    default = "default"
    aggressive = "aggressive"


PRESET_OVERRIDES: dict[str, dict] = {
    "fast": {
        "generation": {"max_depth": 2},
        "mutations": {
            "leet": {"level": 1},
            "case": {"modes": ["lower", "title"]},
            "append": {"numbers_range": [0, 9], "symbols": ["!", "123"]},
        },
    },
    "default": {},
    "aggressive": {
        "generation": {"max_depth": 4},
        "mutations": {
            "leet": {"level": 3},
            "case": {"modes": ["lower", "upper", "title", "toggle", "camel"]},
            "append": {
                "numbers_range": [0, 9999],
                "symbols": ["!", "!!", "123", "1234", "@", "#$%", "!@#"],
            },
            "padding": True,
        },
    },
}


def _get_console():
    from rich.console import Console
    return Console()


def _make_engine(config_path: Optional[Path], preset: str) -> "Engine":
    from cupp.config.loader import load_config, merge_config
    from cupp.core.engine import Engine
    cfg = load_config(config_path)
    if preset != "default" and preset in PRESET_OVERRIDES:
        cfg = merge_config(cfg, PRESET_OVERRIDES[preset])
    return Engine(config=cfg)


@app.command()
def generate(
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive profile input"),
    profile: Optional[Path] = typer.Option(None, "--profile", "-p", help="Profile YAML/JSON file"),
    output: Path = typer.Option(Path("wordlist.txt"), "--output", "-o", help="Output file path"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Config YAML file"),
    preset: Preset = typer.Option(Preset.default, "--preset", help="Generation preset"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Count without writing"),
    stats: bool = typer.Option(True, "--stats/--no-stats", help="Show stats after generation"),
    compress: bool = typer.Option(False, "--compress", "-z", help="Write gzipped output"),
):
    """Generate a password wordlist from a target profile."""
    from rich.console import Console
    from rich.progress import (
        Progress, SpinnerColumn, TextColumn, BarColumn,
        TaskProgressColumn, TimeElapsedColumn,
    )
    from rich.panel import Panel
    console = Console()

    if not interactive and not profile:
        console.print("[red]Error:[/red] Provide --interactive or --profile PATH")
        raise typer.Exit(1)

    engine = _make_engine(config, preset.value)
    console.print(Panel.fit(
        f"[bold green]CUPP v2[/bold green]  |  Rust engine: "
        f"{'[green]ON[/green]' if engine.rust_available() else '[yellow]OFF (Python fallback)[/yellow]'}",
        border_style="green",
    ))

    if interactive:
        from cupp.input.interactive import interactive_profile
        target = interactive_profile()
    else:
        from cupp.input.yaml_loader import load_profile_yaml
        from cupp.input.json_loader import load_profile_json
        assert profile is not None
        if profile.suffix in (".json",):
            target = load_profile_json(profile)
        else:
            target = load_profile_yaml(profile)

    import time
    start = time.perf_counter()
    count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Generating...", total=None)

        if dry_run:
            for _ in engine.generate(target):
                count += 1
                if count % 10_000 == 0:
                    progress.update(task, description=f"Counting: {count:,}")
        else:
            from cupp.output.file_writer import stream_to_file

            out_path = output
            if compress and not str(output).endswith(".gz"):
                out_path = Path(str(output) + ".gz")

            def counting_stream():
                nonlocal count
                for p in engine.generate(target):
                    count += 1
                    if count % 10_000 == 0:
                        progress.update(task, description=f"Generated: {count:,}")
                    yield p

            stream_to_file(counting_stream(), out_path, compress=compress)

    elapsed = time.perf_counter() - start
    speed = count / elapsed if elapsed > 0 else 0

    if stats:
        console.print(f"\n[bold green]Done![/bold green]")
        console.print(f"  Passwords : [cyan]{count:,}[/cyan]")
        console.print(f"  Time      : [cyan]{elapsed:.2f}s[/cyan]")
        console.print(f"  Speed     : [cyan]{speed:,.0f} pass/s[/cyan]")
        if not dry_run:
            console.print(f"  Output    : [cyan]{out_path}[/cyan]")


@app.command()
def enhance(
    wordlist: Path = typer.Argument(..., help="Input wordlist to enhance"),
    output: Path = typer.Option(Path("enhanced.txt"), "--output", "-o"),
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
    preset: Preset = typer.Option(Preset.default, "--preset"),
):
    """Apply mutations to an existing wordlist."""
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
    console = Console()

    engine = _make_engine(config, preset.value)
    from cupp.mutations.leet import LeetMutation
    from cupp.mutations.case import CaseMutation
    from cupp.mutations.append import AppendMutation
    from cupp.filters.dedup import dedup_stream
    from cupp.filters.length import filter_length

    mc = engine.config.mutations
    fc = engine.config.filters
    mutations = [LeetMutation(mc), CaseMutation(mc), AppendMutation(mc)]

    def enhanced_stream():
        with open(wordlist, encoding="utf-8", errors="ignore") as f:
            for line in f:
                word = line.rstrip("\n")
                for mut in mutations:
                    yield from mut.apply(word)

    stream = filter_length(enhanced_stream(), fc.min_length, fc.max_length)
    if fc.dedup:
        stream = dedup_stream(stream, fc.bloom_capacity)

    count = 0
    with Progress(
        SpinnerColumn(), TextColumn("{task.description}"), TimeElapsedColumn(),
        console=console,
    ) as prog:
        task = prog.add_task("Enhancing...", total=None)
        with open(output, "w", encoding="utf-8", buffering=1 << 20) as f:
            for p in stream:
                f.write(p + "\n")
                count += 1
                if count % 10_000 == 0:
                    prog.update(task, description=f"Enhanced: {count:,}")

    console.print(f"[green]Done:[/green] {count:,} passwords -> {output}")


@app.command()
def benchmark(
    iterations: int = typer.Option(100_000, "--iterations", "-n", help="Target passwords to generate"),
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
):
    """Run performance benchmark comparing Python vs Rust engine."""
    from rich.console import Console
    from rich.table import Table
    import time
    console = Console()

    from cupp.core.profile import Profile, DateInfo
    from cupp.config.loader import load_config, merge_config
    from cupp.core.engine import Engine

    test_profile = Profile(
        name="john",
        surname="doe",
        nickname="johnny",
        birthdate=DateInfo(day=15, month=6, year=1990),
        pet_name="rex",
        company="acme",
        keywords=["security", "test"],
    )

    results: dict[str, dict] = {}
    console.print("[yellow]Running benchmark...[/yellow]")

    for label, use_rust in [("Python only", False), ("Python + Rust", True)]:
        cfg = load_config(config)
        cfg = merge_config(cfg, {"generation": {"use_rust_engine": use_rust}})
        engine = Engine(config=cfg)

        start = time.perf_counter()
        count = 0
        for _ in engine.generate(test_profile):
            count += 1
            if count >= iterations:
                break
        elapsed = time.perf_counter() - start
        results[label] = {
            "count": count,
            "elapsed": elapsed,
            "speed": count / elapsed if elapsed > 0 else 0,
        }

    table = Table(
        title="CUPP v2 Benchmark Results",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Engine")
    table.add_column("Passwords", justify="right")
    table.add_column("Time (s)", justify="right")
    table.add_column("Speed (pass/s)", justify="right")
    table.add_column("Speedup", justify="right")

    py_speed = results["Python only"]["speed"]
    for label, data in results.items():
        speedup = (
            f"{data['speed'] / py_speed:.1f}x"
            if py_speed > 0 and label != "Python only"
            else "1.0x"
        )
        table.add_row(
            label,
            f"{data['count']:,}",
            f"{data['elapsed']:.3f}",
            f"{data['speed']:,.0f}",
            speedup,
        )

    console.print(table)


@app.command("strategies")
def strategies_cmd(
    action: str = typer.Argument("list", help="Action: list"),
):
    """Manage generation strategies."""
    from rich.console import Console
    from rich.table import Table
    from cupp.strategies.registry import _REGISTRY
    from cupp.strategies import concatenation, date_based, keyboard_patterns, common_passwords  # noqa: F401
    console = Console()
    table = Table(title="Available Strategies", show_header=True, header_style="bold cyan")
    table.add_column("Name")
    table.add_column("Description")
    for name, cls in _REGISTRY.items():
        table.add_row(name, cls.description)
    console.print(table)


@profile_app.command("init")
def profile_init(
    output: Path = typer.Option(Path("target.yaml"), "--output", "-o"),
):
    """Generate a blank target profile template."""
    template = """\
# CUPP v2 Target Profile
# Fill in the information you know about the target.
# Leave fields blank or remove them if unknown.

name: ""               # First name (e.g. "john")
surname: ""            # Surname (e.g. "doe")
nickname: ""           # Common nickname
birthdate:
  day: null            # 1-31
  month: null          # 1-12
  year: null           # e.g. 1990

partner_name: ""
partner_nickname: ""
partner_birthdate:
  day: null
  month: null
  year: null

child_name: ""
child_nickname: ""
child_birthdate:
  day: null
  month: null
  year: null

pet_name: ""
company: ""            # Workplace name
phone: ""              # Phone number (digits only recommended)

keywords:              # Any other relevant words
  - ""
"""
    with open(output, "w") as f:
        f.write(template)
    typer.echo(f"Profile template written to: {output}")


@app.command("config")
def config_cmd(
    action: str = typer.Argument("validate"),
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
):
    """Validate configuration file."""
    from rich.console import Console
    console = Console()
    try:
        from cupp.config.loader import load_config
        cfg = load_config(config)
        console.print(f"[green]Config valid:[/green] {config or 'default'}")
        console.print(f"  Strategies  : {cfg.strategies.enabled}")
        console.print(f"  Leet level  : {cfg.mutations.leet.level}")
        console.print(f"  Max depth   : {cfg.generation.max_depth}")
        console.print(f"  Length      : {cfg.filters.min_length}-{cfg.filters.max_length}")
    except Exception as e:
        console.print(f"[red]Config invalid:[/red] {e}")
        raise typer.Exit(1)


def main():
    app()


if __name__ == "__main__":
    main()
