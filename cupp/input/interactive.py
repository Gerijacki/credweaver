from typing import Optional
from cupp.core.profile import Profile, DateInfo


def _ask(prompt: str, required: bool = False) -> Optional[str]:
    try:
        from rich.prompt import Prompt
        val = Prompt.ask(f"[cyan]{prompt}[/cyan]", default="")
    except ImportError:
        val = input(f"{prompt}: ")
    return val.strip() if val.strip() else None


def _ask_date(label: str) -> Optional[DateInfo]:
    raw = _ask(f"{label} (DD/MM/YYYY or leave blank)")
    if not raw:
        return None
    parts = raw.replace("-", "/").split("/")
    if len(parts) == 3:
        try:
            return DateInfo(day=int(parts[0]), month=int(parts[1]), year=int(parts[2]))
        except (ValueError, Exception):
            pass
    elif len(parts) == 1 and len(raw) == 4:
        try:
            return DateInfo(year=int(raw))
        except ValueError:
            pass
    return None


def interactive_profile() -> Profile:
    try:
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
        console.print(Panel.fit(
            "[bold green]CUPP v2[/bold green] - [yellow]Target Profiling[/yellow]\n"
            "[dim]Fill in as much information as you know about the target.[/dim]",
            border_style="green",
        ))
    except ImportError:
        print("=== CUPP v2 - Target Profiling ===")

    name = _ask("First name")
    surname = _ask("Surname")
    nickname = _ask("Nickname")
    birthdate = _ask_date("Birthdate")
    partner_name = _ask("Partner's first name")
    partner_nickname = _ask("Partner's nickname")
    partner_birthdate = _ask_date("Partner's birthdate")
    child_name = _ask("Child's name")
    child_nickname = _ask("Child's nickname")
    child_birthdate = _ask_date("Child's birthdate")
    pet_name = _ask("Pet's name")
    company = _ask("Company/workplace")
    phone = _ask("Phone number")
    keywords_raw = _ask("Additional keywords (comma-separated)")
    keywords = [k.strip() for k in keywords_raw.split(",")] if keywords_raw else []

    return Profile(
        name=name,
        surname=surname,
        nickname=nickname,
        birthdate=birthdate,
        partner_name=partner_name,
        partner_nickname=partner_nickname,
        partner_birthdate=partner_birthdate,
        child_name=child_name,
        child_nickname=child_nickname,
        child_birthdate=child_birthdate,
        pet_name=pet_name,
        company=company,
        phone=phone,
        keywords=keywords,
    )
