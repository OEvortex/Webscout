import argparse
import sys
import webscout.Provider
from webscout.Provider import __all__ as PROVIDER_ALL
from webscout.AIbase import Provider as BaseProvider
import inspect
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
import json

console = Console()

def list_providers():
    # Access the module directly from sys.modules to avoid shadowing
    provider_module = sys.modules['webscout.Provider']
    console.print(f"[yellow]DEBUG: PROVIDER_ALL has {len(PROVIDER_ALL)} items[/yellow]")
    console.print(f"[yellow]DEBUG: provider_module is {provider_module}[/yellow]")
    table = Table(title="Webscout Providers")
    table.add_column("Name", style="cyan")
    table.add_column("Auth Required", style="magenta")
    table.add_column("Models", style="green")

    for name in PROVIDER_ALL:
        provider_cls = getattr(provider_module, name, None)
        if provider_cls and inspect.isclass(provider_cls) and issubclass(provider_cls, BaseProvider):
            auth = getattr(provider_cls, "required_auth", "Unknown")
            models = getattr(provider_cls, "AVAILABLE_MODELS", [])
            models_str = ", ".join(models[:3]) + ("..." if len(models) > 3 else "")
            table.add_row(name, str(auth), models_str)
    
    console.print(table)

def test_provider(provider_name, model=None, prompt="Say 'Hello World' in one word", stream=False, api_key=None):
    provider_module = sys.modules['webscout.Provider']
    provider_cls = getattr(provider_module, provider_name, None)
    if not provider_cls:
        console.print(f"[red]Provider {provider_name} not found.[/red]")
        return

    console.print(f"[yellow]Testing provider: {provider_name}[/yellow]")
    
    # Prepare initialization arguments
    init_args = {}
    if getattr(provider_cls, "required_auth", False):
        if not api_key:
            console.print(f"[red]Provider {provider_name} requires an API key. Use --api-key.[/red]")
            return
        # Some providers use 'api_key', some might use something else.
        # Most use 'api_key' in __init__.
        init_args["api_key"] = api_key
    
    if model:
        init_args["model"] = model

    try:
        # Try to initialize. Some might need more args.
        # We'll try to catch common errors.
        provider = None
        try:
            provider = provider_cls(**init_args)
        except TypeError as e:
            console.print(f"[red]Initialization failed: {e}[/red]")
            console.print("[yellow]Hint: This provider might require specific arguments (e.g. cookie_file).[/yellow]")
            return

        if not provider:
            return

        console.print(f"[blue]Prompt: {prompt}[/blue]")
        
        if stream:
            console.print("[blue]Streaming response:[/blue]")
            full_response = ""
            with Live(Panel("", title="Response"), refresh_per_second=10) as live:
                for chunk in provider.chat(prompt, stream=True):
                    if isinstance(chunk, dict):
                        text = chunk.get("text", "")
                    else:
                        text = str(chunk)
                    full_response += text
                    live.update(Panel(full_response, title="Response"))
            console.print("\n[green]Stream completed.[/green]")
        else:
            response = provider.chat(prompt, stream=False)
            console.print(Panel(str(response), title="Response"))
            
    except Exception as e:
        console.print(f"[red]Error during test: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())

def test_all_providers(api_keys=None, prompt="Say 'Hello World' in one word"):
    provider_module = sys.modules['webscout.Provider']
    results = []
    
    console.print(f"[yellow]Testing all {len(PROVIDER_ALL)} providers...[/yellow]")
    
    for name in PROVIDER_ALL:
        provider_cls = getattr(provider_module, name, None)
        if not provider_cls or not inspect.isclass(provider_cls) or not issubclass(provider_cls, BaseProvider):
            continue

        auth_required = getattr(provider_cls, "required_auth", False)
        api_key = None
        if auth_required:
            if api_keys and name in api_keys:
                api_key = api_keys[name]
            elif api_keys and "default" in api_keys:
                api_key = api_keys["default"]
            else:
                results.append({"name": name, "status": "Skipped (No API Key)", "error": None})
                continue

        console.print(f"Testing {name}...", end=" ")
        try:
            # Try to initialize
            init_args = {}
            if auth_required:
                init_args["api_key"] = api_key
            
            # Special case for Gemini which needs cookie_file
            if name == "GEMINI":
                results.append({"name": name, "status": "Skipped (Needs cookie file)", "error": None})
                console.print("[yellow]Skipped[/yellow]")
                continue

            provider = provider_cls(**init_args)
            response = provider.chat(prompt, stream=False)
            
            if response:
                results.append({"name": name, "status": "Working", "error": None})
                console.print("[green]Working[/green]")
            else:
                results.append({"name": name, "status": "Empty Response", "error": None})
                console.print("[red]Empty Response[/red]")
                
        except Exception as e:
            results.append({"name": name, "status": "Failed", "error": str(e)})
            console.print(f"[red]Failed: {e}[/red]")

    # Print summary table
    table = Table(title="Webscout Live Test Results")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Error", style="red")

    for res in results:
        table.add_row(res["name"], res["status"], res["error"] or "")
    
    console.print(table)

def test_provider_models(provider_name, api_key=None, prompt="Say 'Hello World' in one word"):
    provider_module = sys.modules['webscout.Provider']
    provider_cls = getattr(provider_module, provider_name, None)
    if not provider_cls:
        console.print(f"[red]Provider {provider_name} not found.[/red]")
        return

    models = getattr(provider_cls, "AVAILABLE_MODELS", [])
    if not models:
        console.print(f"[yellow]No models found for {provider_name}. Testing default...[/yellow]")
        test_provider(provider_name, prompt=prompt, api_key=api_key)
        return

    console.print(f"[yellow]Testing {len(models)} models for {provider_name}...[/yellow]")
    results = []
    for model in models:
        console.print(f"Testing model {model}...", end=" ")
        try:
            init_args = {"model": model}
            if getattr(provider_cls, "required_auth", False):
                init_args["api_key"] = api_key
            
            provider = provider_cls(**init_args)
            response = provider.chat(prompt, stream=False)
            
            if response:
                results.append({"model": model, "status": "Working"})
                console.print("[green]Working[/green]")
            else:
                results.append({"model": model, "status": "Empty Response"})
                console.print("[red]Empty Response[/red]")
        except Exception as e:
            results.append({"model": model, "status": f"Failed: {e}"})
            console.print(f"[red]Failed: {e}[/red]")

    table = Table(title=f"Model Test Results for {provider_name}")
    table.add_column("Model", style="cyan")
    table.add_column("Status", style="magenta")
    for res in results:
        table.add_row(res["model"], res["status"])
    console.print(table)

def main():
    parser = argparse.ArgumentParser(description="Webscout Live Provider Tester")
    parser.add_argument("--list", action="store_true", help="List all available providers")
    parser.add_argument("--test-all", action="store_true", help="Test all providers (live)")
    parser.add_argument("--test-models", action="store_true", help="Test all models of a specific provider")
    parser.add_argument("--api-keys-file", type=str, help="JSON file with API keys for providers")
    parser.add_argument("--provider", type=str, help="Provider name to test")
    parser.add_argument("--model", type=str, help="Model name to test")
    parser.add_argument("--prompt", type=str, default="Say 'Hello World' in one word", help="Prompt to send")
    parser.add_argument("--stream", action="store_true", help="Use streaming")
    parser.add_argument("--api-key", type=str, help="API key if required")

    args = parser.parse_args()

    api_keys = {}
    if args.api_keys_file:
        try:
            with open(args.api_keys_file, "r") as f:
                api_keys = json.load(f)
        except Exception as e:
            console.print(f"[red]Failed to load API keys file: {e}[/red]")

    if args.list:
        list_providers()
    elif args.test_all:
        test_all_providers(api_keys, args.prompt)
    elif args.provider:
        if args.test_models:
            test_provider_models(args.provider, args.api_key or api_keys.get(args.provider), args.prompt)
        else:
            test_provider(args.provider, args.model, args.prompt, args.stream, args.api_key or api_keys.get(args.provider))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
