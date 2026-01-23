import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from rich.console import Console
from rich.table import Table

from webscout.Provider.Ayle import Ayle

console = Console()

# This is an interactive model tester (not a unit test). Skip when running pytest.
pytestmark = pytest.mark.skip(reason="Interactive provider check — run manually instead of via pytest")

def test_model(model_name):
    try:
        ai = Ayle(model=model_name, timeout=15)
        # Just a very short prompt to check if it responds
        response = ai.chat("hi", stream=False)

        content = ""
        if isinstance(response, str):
            content = response
        elif hasattr(response, "__iter__"):
            content = "".join(list(response))

        if content and len(content.strip()) > 0:
            return model_name, True, "Success"
        else:
            return model_name, False, "Empty response"
    except Exception as e:
        return model_name, False, str(e)

def main():
    ai = Ayle()
    models = ai.AVAILABLE_MODELS

    results = []
    console.print(f"[bold blue]Testing {len(models)} models from Ayle...[/bold blue]")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(test_model, model): model for model in models}
        for future in as_completed(futures):
            results.append(future.result())
            model_name, success, info = results[-1]
            status = "[green]PASS[/green]" if success else "[red]FAIL[/red]"
            console.print(f"{status} {model_name}: {info}")

    table = Table(title="Ayle Model Status")
    table.add_column("Model", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Info", style="dim")

    working_models = []
    for model_name, success, info in sorted(results):
        status = "Working" if success else "Failed"
        table.add_row(model_name, status, info)
        if success:
            working_models.append(model_name)

    console.print(table)

    print("\nWorking models (copy-paste):")
    print(working_models)

if __name__ == "__main__":
    main()
