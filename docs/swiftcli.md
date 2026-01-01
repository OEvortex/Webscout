<div align="center">
  
# ⚡ SwiftCLI

> Build Beautiful Command-Line Applications at Light Speed

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![PyPI version](https://img.shields.io/badge/View_on-PyPI-orange.svg?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/webscout/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)


</div>

## 🌟 Key Features

- 🎨 **Rich Output**: Beautiful tables, progress bars, and styled text
- 🔄 **Command Groups**: Organize commands logically
- 🎯 **Type Safety**: Full type hints and runtime validation
- 🔌 **Plugin System**: Extend functionality easily
- 🌍 **Environment Support**: Load config from env vars and files
- 🚀 **Modern Python**: Async support, type hints, and more
- 🔍 **Advanced Validation**: Argument and option validation with patterns, ranges, and choices
- 🔗 **Command Chaining**: Chain commands together with result passing
- 🏷️ **Command Aliases**: Create shortcuts for frequently used commands
- 🐚 **Shell Completion**: Generate completion scripts for bash, zsh, and fish
- 📋 **Mutually Exclusive Options**: Prevent conflicting option combinations
- 📄 **Multiple Output Formats**: JSON, YAML, and custom formatters

## 📦 Installation

```bash
pip install -U webscout
```

## 🚀 Quick Start

```python
from webscout.swiftcli import CLI, option, table_output

app = CLI("myapp", version="1.0.0")

@app.command()
@option("--count", "-c", type=int, default=5)
@table_output(["ID", "Status"])
def list_items(count: int):
    """List system items with status"""
    return [
        [i, "Active" if i % 2 == 0 else "Inactive"]
        for i in range(1, count + 1)
    ]

if __name__ == "__main__":
    app.run()
```

Run it:
```bash
$ python app.py list-items --count 3
┌────┬──────────┐
│ ID │ Status   │
├────┼──────────┤
│ 1  │ Inactive │
│ 2  │ Active   │
│ 3  │ Inactive │
└────┴──────────┘
```

## 🎯 Advanced Validation

SwiftCLI now supports comprehensive argument and option validation:

```python
@app.command()
@option("--name", type=str, validation={'min_length': 3, 'max_length': 20})
@option("--age", type=int, validation={'min': 18, 'max': 120})
@option("--email", type=str, validation={'pattern': r'^[^@]+@[^@]+\.[^@]+$'})
@argument("action", validation={'choices': ["create", "update", "delete"]})
def user_management(name: str, age: int, email: str, action: str):
    """Manage users with validation"""
    return {"name": name, "age": age, "email": email, "action": action}
```

## 📄 Multiple Output Formats

Choose from table, JSON, or YAML output:

```python
# JSON output
@app.command()
@json_output(indent=2)
def get_data():
    return {"status": "success", "data": [1, 2, 3]}

# YAML output
@app.command()
@yaml_output()
def get_config():
    return {"database": {"host": "localhost", "port": 5432}}
```

## 🏷️ Command Aliases

Create shortcuts for frequently used commands:

```python
app.alias("list", "ls")
app.alias("show", "display")
```

## 🐚 Shell Completion

Generate completion scripts for your shell:

```python
# Generate completion scripts
with open("completion.bash", "w") as f:
    f.write(app.generate_completion_script('bash'))

with open("completion.zsh", "w") as f:
    f.write(app.generate_completion_script('zsh'))

with open("completion.fish", "w") as f:
    f.write(app.generate_completion_script('fish'))
```

## 🔗 Command Chaining

Enable command chaining for complex workflows:

```python
app.enable_chaining(True)

@app.command()
def step1():
    return {"data": "from step1"}

@app.command()
def step2(data: dict):
    return {"result": f"Processed {data['data']}"}
```

## 📋 Mutually Exclusive Options

Prevent conflicting option combinations:

```python
@app.command()
@option("--verbose", is_flag=True, mutually_exclusive=["quiet"])
@option("--quiet", is_flag=True, mutually_exclusive=["verbose"])
def process(verbose: bool, quiet: bool):
    """Process with mutually exclusive options"""
    pass
```

## 📚 Documentation

### Command Groups

Organize related commands:

```python
@app.group()
def db():
    """Database operations"""
    pass

@db.command()
@option("--force", is_flag=True)
def migrate(force: bool):
    """Run database migrations"""
    print(f"Running migrations (force={force})")

# Usage: python app.py db migrate --force
```

### Rich Output

Beautiful progress bars and tables:

```python
@app.command()
@progress("Processing")
async def process():
    """Process items with progress"""
    for i in range(5):
        yield f"Step {i+1}/5"
        await asyncio.sleep(0.5)

@app.command()
@table_output(["Name", "Score"])
def top_scores():
    """Show top scores"""
    return [
        ["Alice", 100],
        ["Bob", 95],
        ["Charlie", 90]
    ]
```

### Type-Safe Options

```python
from enum import Enum
from datetime import datetime
from typing import List, Optional

class Format(Enum):
    JSON = "json"
    YAML = "yaml"
    CSV = "csv"

@app.command()
@option("--format", type=Format, default=Format.JSON)
@option("--date", type=datetime)
@option("--tags", type=List[str])
def export(
    format: Format,
    date: datetime,
    tags: Optional[List[str]] = None
):
    """Export data with type validation"""
    print(f"Exporting as {format.value}")
    print(f"Date: {date}")
    if tags:
        print(f"Tags: {', '.join(tags)}")
```

### Environment & Config

```python
@app.command()
@envvar("API_KEY", required=True)
@config_file("~/.config/myapp.yaml")
def api_call(api_key: str, config: dict):
    """Make API call using config"""
    url = config.get("api_url")
    print(f"Calling {url} with key {api_key[:4]}...")
```

### Async Support

```python
@app.command()
async def fetch_data():
    """Fetch data asynchronously"""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.example.com") as resp:
            data = await resp.json()
            return data
```

### Plugin System

```python
from webscout.swiftcli import Plugin

class MetricsPlugin(Plugin):
    def __init__(self):
        self.start_time = None
        
    def before_command(self, command: str, args: list):
        self.start_time = time.time()
        
    def after_command(self, command: str, args: list, result: any):
        duration = time.time() - self.start_time
        print(f"Command {command} took {duration:.2f}s")

app.plugin_manager.register(MetricsPlugin())
```

## 🛠 Advanced Features

### Custom Output Formatting

```python
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

@app.command()
def status():
    """Show system status"""
    table = Table(show_header=True)
    table.add_column("Service")
    table.add_column("Status")
    table.add_column("Uptime")
    
    table.add_row("API", "✅ Online", "24h")
    table.add_row("DB", "✅ Online", "12h")
    table.add_row("Cache", "⚠️ Degraded", "6h")
    
    console.print(Panel(
        table,
        title="System Status",
        border_style="green"
    ))
```

### Command Pipelines

```python
@app.group(chain=True)
def process():
    """Data processing pipeline"""
    pass

@process.command()
def extract():
    """Extract data"""
    return {"data": [1, 2, 3]}

@process.command()
def transform(data: dict):
    """Transform data"""
    return {"data": [x * 2 for x in data["data"]]}

@process.command()
def load(data: dict):
    """Load data"""
    print(f"Loading: {data}")

# Usage: python app.py process extract transform load
```

## 🔧 Configuration

### Application Config

```python
app = CLI(
    name="myapp",
    version="1.0.0",
    description="My awesome CLI app",
    config_file="~/.config/myapp.yaml",
    auto_envvar_prefix="MYAPP",
    plugin_folder="~/.myapp/plugins"
)
```

### Command Config

```python
@app.command()
@option("--config", type=click.Path(exists=True))
@option("--verbose", "-v", count=True)
@option("--format", type=click.Choice(["json", "yaml"]))
def process(config: str, verbose: int, format: str):
    """Process with configuration"""
    pass
```

## 📋 Best Practices

1. **Use Type Hints**
   ```python
   from typing import Optional, List, Dict
   
   @app.command()
   def search(
       query: str,
       limit: Optional[int] = 10,
       tags: List[str] = None
   ) -> Dict[str, any]:
       """Search with proper type hints"""
       pass
   ```

2. **Structured Error Handling**
   ```python
   from webscout.swiftcli import CLIError
   
   @app.command()
   def risky():
       try:
           # Risky operation
           pass
       except FileNotFoundError as e:
           raise CLIError("Config file not found") from e
       except PermissionError as e:
           raise CLIError("Permission denied") from e
   ```

3. **Command Organization**
   ```python
   # commands/
   # ├── __init__.py
   # ├── db.py
   # ├── auth.py
   # └── utils.py
   
   from .commands import db, auth, utils
   
   app.add_command_group(db.commands)
   app.add_command_group(auth.commands)
   app.add_command_group(utils.commands)
   ```

## 🤝 Contributing

Contributions are welcome! Check out our [Contributing Guide](CONTRIBUTING.md) for details.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

<div align="center">

---

Made with ❤️ by the [Webscout](https://github.com/OEvortex/Webscout) team

[![GitHub stars](https://img.shields.io/github/stars/OEvortex/Webscout?style=social)](https://github.com/OEvortex/Webscout)

</div>

## Changelog (selected fixes/enhancements)

- Fix: parse_args now accepts --key=value and -k=value syntax, and accumulates repeated options into lists
- Fix: convert_type handles boolean inputs and list-typed values robustly
- Fix: CLI now supports 'count' and 'multiple' option attributes, and validates 'choices' for multiple options
- Fix: CLI and Group run now inject Context object with @pass_context decorator
- Fix: CLI and Group run support async (coroutine) commands
- Enhancement: Help output deduplicates commands and prints aliases neatly
- Enhancement: Option decorator now distinguishes unspecified default vs explicit default using a sentinel
- Tests: Added multiple unit tests to cover parsing, options, flags, groups, plugins, and async commands

