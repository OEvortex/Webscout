import argparse
import inspect
import json
import sys

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from llm4free import AISEARCH, STT, TTI, TTS, llm
from llm4free.AIbase import Provider as BaseProvider

console = Console()


# Collect all provider classes from all packages
def _collect_providers():
    providers = {}
    for package in [llm, AISEARCH, STT, TTI, TTS]:
        for name in getattr(package, "__all__", []):
            cls = getattr(package, name, None)
            if cls and inspect.isclass(cls) and issubclass(cls, BaseProvider):
                providers[name] = cls
    return providers


PROVIDER_MAP = _collect_providers()
PROVIDER_ALL = list(PROVIDER_MAP.keys())


def list_providers():
    console.print(f"[yellow]DEBUG: PROVIDER_ALL has {len(PROVIDER_ALL)} items[/yellow]")
    table = Table(title="Webscout Providers")
    table.add_column("Name", style="cyan")
    table.add_column("Auth Required", style="magenta")
    table.add_column("Models", style="green")

    for name in PROVIDER_ALL:
        provider_cls = PROVIDER_MAP.get(name)
        if provider_cls:
            auth = getattr(provider_cls, "required_auth", "Unknown")
            models = getattr(provider_cls, "AVAILABLE_MODELS", [])
            models_str = ", ".join(models[:3]) + ("..." if len(models) > 3 else "")
            table.add_row(name, str(auth), models_str)

    console.print(table)


def run_provider(
    provider_name, model=None, prompt="Say 'Hello World' in one word", stream=False, api_key=None
):
    provider_cls = PROVIDER_MAP.get(provider_name)
    if not provider_cls:
        console.print(f"[red]Provider {provider_name} not found.[/red]")
        return

    console.print(f"[yellow]Testing provider: {provider_name}[/yellow]")

    # Prepare initialization arguments
    init_args = {}
    if getattr(provider_cls, "required_auth", False):
        if not api_key:
            console.print(
                f"[red]Provider {provider_name} requires an API key. Use --api-key.[/red]"
            )
            return
        init_args["api_key"] = api_key

    # Add model if provided
    if model:
        init_args["model"] = model

    try:
        provider = provider_cls(**init_args)

        if stream:
            console.print("[green]Streaming response:[/green]")
            response = provider.ask(prompt, stream=True)
            full_response = ""
            for chunk in response:
                if isinstance(chunk, dict):
                    text = chunk.get("text", chunk.get("content", str(chunk)))
                else:
                    text = str(chunk)
                print(text, end="", flush=True)
                full_response += text
            print()  # New line after streaming
            return full_response
        else:
            response = provider.ask(prompt, stream=False)
            if isinstance(response, dict):
                text = response.get("text", response.get("content", str(response)))
            else:
                text = str(response)
            console.print(f"[green]Response:[/green] {text}")
            return text
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return None


def run_all_providers(prompt="Say 'Hello World' in one word", api_key=None):
    results = []
    for provider_name in PROVIDER_ALL:
        auth_required = getattr(PROVIDER_MAP[provider_name], "required_auth", False)
        if auth_required and not api_key:
            results.append((provider_name, "SKIPPED", "Requires API key"))
            continue

        try:
            response = run_provider(provider_name, prompt=prompt, api_key=api_key)
            if response:
                results.append((provider_name, "WORKING", response[:100]))
            else:
                results.append((provider_name, "FAILED", "No response"))
        except Exception as e:
            results.append((provider_name, "ERROR", str(e)[:100]))

    return results


def main():
    parser = argparse.ArgumentParser(description="Webscout Provider Tester")
    parser.add_argument("--list", action="store_true", help="List all providers")
    parser.add_argument("--provider", type=str, help="Test a specific provider")
    parser.add_argument("--model", type=str, help="Model to use")
    parser.add_argument(
        "--prompt", type=str, default="Say 'Hello World' in one word", help="Prompt to send"
    )
    parser.add_argument("--stream", action="store_true", help="Enable streaming")
    parser.add_argument("--api-key", type=str, help="API key for providers that require it")
    parser.add_argument("--test-all", action="store_true", help="Test all providers")

    args = parser.parse_args()

    if args.list:
        list_providers()
    elif args.provider:
        run_provider(
            args.provider,
            model=args.model,
            prompt=args.prompt,
            stream=args.stream,
            api_key=args.api_key,
        )
    elif args.test_all:
        results = run_all_providers(prompt=args.prompt, api_key=args.api_key)

        table = Table(title="Provider Test Results")
        table.add_column("Provider", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Result", style="green")

        for name, status, result in results:
            status_color = (
                "green" if status == "WORKING" else "red" if status == "ERROR" else "yellow"
            )
            table.add_row(name, f"[{status_color}]{status}[/{status_color}]", result)

        console.print(table)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
