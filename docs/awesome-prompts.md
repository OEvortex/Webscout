# 🚀 Webscout Awesome Prompts Manager
> Last updated: 2025-12-20
> Maintained by [Webscout](https://github.com/OEvortex/Webscout)

Webscout's Awesome Prompts Manager provides a comprehensive system for managing and utilizing AI personas and specialized prompts. This module offers optimized prompt retrieval, caching, and management capabilities for enhanced AI interactions.

## Table of Contents

1. [Core Components](#core-components)
2. [Prompt Manager](#prompt-manager)
3. [Configuration Options](#configuration-options)
4. [Usage Examples](#usage-examples)
5. [Prompt Categories](#prompt-categories)
6. [Advanced Features](#advanced-features)
7. [Integration Guide](#integration-guide)

## Core Components

### [`prompt_manager.py`](../webscout/prompt_manager.py:1)

The main prompt management module that provides comprehensive prompt handling capabilities.

```python
from webscout.prompt_manager import AwesomePrompts

# Initialize the prompt manager
prompt_manager = AwesomePrompts()

# Get a specific prompt
prompt = prompt_manager.get_act("UX/UI Developer")
print(prompt)
```

**Key Features:**
- Optimized prompt retrieval with LRU caching
- Automatic updates from online repository
- Thread-safe operations with proper locking
- Efficient prompt management and indexing
- Support for both string and numeric key access
- Comprehensive error handling and validation

## Prompt Manager

### [`AwesomePrompts` Class](../webscout/prompt_manager.py:22)

The main class for managing awesome prompts with caching and optimization.

```python
from webscout.prompt_manager import AwesomePrompts

# Initialize with default settings
prompt_manager = AwesomePrompts()

# Or with custom configuration
custom_manager = AwesomePrompts(
    repo_url="https://custom-repo.com/prompts.json",
    local_path="/custom/path/prompts.json",
    auto_update=False,
    cache_size=256
)
```

**Main Methods:**

| Method | Description |
|--------|-------------|
| `get_act(key, default=None, case_insensitive=True, use_cache=True)` | Get a prompt by name or index |
| `add_prompt(name, prompt, validate=True)` | Add a new prompt to the collection |
| `delete_prompt(name, case_insensitive=True, raise_not_found=False)` | Delete a prompt from the collection |
| `update_prompts_from_online(force=False)` | Update prompts from the online repository |
| `show_acts(search=None, limit=100)` | Display available prompts with filtering |
| `get_random_act()` | Get a random prompt from the collection |

## Configuration Options

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `repo_url` | `str` | `"https://raw.githubusercontent.com/OEvortex/prompts/main/prompt.json"` | URL to fetch prompts from |
| `local_path` | `Optional[str]` | `~/.webscout/awesome-prompts.json` | Where to save prompts locally |
| `auto_update` | `bool` | `True` | Auto update prompts on initialization |
| `timeout` | `int` | `10` | Timeout for HTTP requests in seconds |
| `impersonate` | `str` | `"chrome110"` | Browser profile for curl_cffi |
| `cache_size` | `int` | `128` | LRU cache size for get operations |
| `max_workers` | `int` | `4` | Maximum threads for concurrent operations |

## Usage Examples

### Basic Usage

```python
from webscout.prompt_manager import AwesomePrompts

# Initialize the prompt manager
prompt_manager = AwesomePrompts()

# Get a prompt by name
ux_prompt = prompt_manager.get_act("UX/UI Developer")
print(ux_prompt)

# Get a prompt by index
first_prompt = prompt_manager.get_act(0)
print(first_prompt)
```

### Adding Custom Prompts

```python
# Add a new custom prompt
success = prompt_manager.add_prompt(
    "Custom Developer",
    "I want you to act as a custom software developer specialized in Python and AI applications."
)

if success:
    # Use the newly added prompt
    custom_prompt = prompt_manager.get_act("Custom Developer")
    print(custom_prompt)
```

### Managing Prompts

```python
# List all available prompts
prompt_manager.show_acts()

# Search for specific prompts
prompt_manager.show_acts(search="developer")

# Delete a prompt
prompt_manager.delete_prompt("Custom Developer")

# Get a random prompt
random_prompt = prompt_manager.get_random_act()
print(random_prompt)
```

### Advanced Configuration

```python
# Custom configuration with larger cache
advanced_manager = AwesomePrompts(
    repo_url="https://custom-repo.com/prompts.json",
    local_path="/custom/path/prompts.json",
    auto_update=True,
    cache_size=512,
    timeout=30,
    max_workers=8
)

# Force update from repository
advanced_manager.update_prompts_from_online(force=True)
```

### Using with Webscout Providers

```python
from webscout.Provider import ChatGPT
from webscout.prompt_manager import AwesomePrompts

# Initialize both components
prompt_manager = AwesomePrompts()
provider = ChatGPT()

# Get a specialized prompt
tech_writer_prompt = prompt_manager.get_act("Tech Writer")

# Use the prompt with a provider
response = provider.ask(f"{tech_writer_prompt}\n\nPlease write documentation for a new AI API.")
print(response)
```

## Prompt Categories

The Awesome Prompts collection contains 240+ prompts organized into 9 categories:

<div align="center">

| Category | Description | Count |
|---------|-------------|-------:|
| [💻 Development & Technical](#-development--technical) | Software development, cybersecurity, and IT roles | 10 |
| [🧩 Programming Environments](#-programming-environments) | Interactive coding environments and interpreters | 10 |
| [📝 Writing & Content Creation](#-writing--content-creation) | Content writing, translation, and creative text generation | 16 |
| [🎓 Education & Learning](#-education--learning) | Teaching, tutoring, and educational content | 13 |
| [💼 Professional Roles](#-professional-roles) | Business, healthcare, and specialized professional personas | 17 |
| [🎭 Entertainment & Creative](#-entertainment--creative) | Creative arts, games, and entertainment | 22 |
| [🧠 Advisors & Coaches](#-advisors--coaches) | Personal guidance, coaching, and advisory roles | 83 |
| [🌐 Alternative Models](#-alternative-models) | Experimental and alternative AI interaction models | 79 |
| [🔮 Specialized Assistants](#-specialized-assistants) | Niche and specialized helper roles | 11 |

</div>

## 💻 Development & Technical

<details open>
<summary><strong>Software Development & IT Roles</strong></summary>

| Index | Name | Preview |
|-------|------|---------|
| 31 | UX/UI Developer | I want you to act as a UX/UI developer. I will provide... |
| 32 | Cyber Security Specialist | I want you to act as a cyber security specialist... |
| 73 | IT Architect | I want you to act as an IT Architect. I will provide... |
| 109 | Machine Learning Engineer | I want you to act as a machine learning engineer... |
| 112 | IT Expert | I want you to act as an IT Expert. I will provide... |
| 115 | Fullstack Software Developer | I want you to act as a software developer. I will... |
| 127 | Software Quality Assurance Tester | I want you to act as a software quality assurance... |
| 132 | Senior Frontend Developer | I want you to act as a Senior Frontend developer... |
| 242 | Ethereum Developer | Imagine you are an experienced Ethereum developer... |
| 245 | Data Scientist | I want you to act as a data scientist. Imagine you... |

</details>

## 🧩 Programming Environments

<details open>
<summary><strong>Interactive Coding & Development Environments</strong></summary>

| Index | Name | Preview |
|-------|------|---------|
| 2 | Linux Terminal | I want you to act as a linux terminal. I will type... |
| 5 | JavaScript Console | I want you to act as a javascript console. I will... |
| 6 | Excel Sheet | I want you to act as a text based excel. you'll on... |
| 66 | SQL Terminal | I want you to act as a SQL terminal in front of an... |
| 101 | Python Interpreter | I want you to act like a Python interpreter. I will... |
| 121 | R Programming Interpreter | I want you to act as a R interpreter. I'll type co... |
| 124 | PHP Interpreter | I want you to act like a php interpreter. I will w... |
| 131 | Web Browser | I want you to act as a text based web browser brow... |
| 133 | Solr Search Engine | I want you to act as a Solr Search Engine running... |
| 157 | Python Interpreter | Act as a Python interpreter. I will give you comma... |

</details>

## 📝 Writing & Content Creation

<details open>
<summary><strong>Writing, Translation & Creative Content</strong></summary>

| Index | Name | Preview |
|-------|------|---------|
| 3 | English Translator and Improver | I want you to act as an English translator, spelli... |
| 8 | Spoken English Teacher and Improver | I want you to act as a spoken English teacher and... |
| 13 | Storyteller | I want you to act as a storyteller. You will come... |
| 20 | Screenwriter | I want you to act as a screenwriter. You will deve... |
| 21 | Novelist | I want you to act as a novelist. You will come up... |
| 24 | Poet | I want you to act as a poet. You will create poems... |
| 25 | Rapper | I want you to act as a rapper. You will come up wi... |
| 84 | Essay Writer | I want you to act as an essay writer. You will nee... |
| 94 | Journalist | I want you to act as a journalist. You will report... |
| 99 | Tech Writer | I want you to act as a tech writer. You will act a... |
| 138 | Commit Message Generator | I want you to act as a commit message generator. I... |
| 143 | Title Generator for Written Pieces | I want you to act as a title generator for written... |
| 148 | Cover Letter | In order to submit applications for jobs, I want t... |
| 152 | Proofreader | I want you act as a proofreader. I will provide yo... |
| 243 | SEO Prompt | Using WebPilot, create an outline for an article t... |
| 244 | Prompt Enhancer | Act as a Prompt Enhancer AI that takes user-input... |

</details>

## 🎓 Education & Learning

<details open>
<summary><strong>Teaching & Educational Assistance</strong></summary>

| Index | Name | Preview |
|-------|------|---------|
| 7 | English Pronunciation Helper | I want you to act as an English pronunciation assi... |
| 27 | Philosophy Teacher | I want you to act as a philosophy teacher. I will... |
| 28 | Philosopher | I want you to act as a philosopher. I will provide... |
| 29 | Math Teacher | I want you to act as a math teacher. I will provid... |
| 30 | AI Writing Tutor | I want you to act as an AI writing tutor. I will p... |
| 65 | Instructor in a School | I want you to act as an instructor in a school, te... |
| 82 | Educational Content Creator | I want you to act as an educational content creato... |
| 116 | Mathematician | I want you to act like a mathematician. I will typ... |
| 146 | Mathematical History Teacher | I want you to act as a mathematical history teache... |
| 159 | Wikipedia Page | I want you to act as a Wikipedia page. I will give... |
| 160 | Japanese Kanji Quiz Machine | I want you to act as a Japanese Kanji quiz machine... |
| 161 | Note-taking Assistant | I want you to act as a note-taking assistant for a... |
| 162 | Literary Critic | I want you to act as a `language` literary critic.... |

</details>

## 💼 Professional Roles

<details open>
<summary><strong>Business, Healthcare & Professional Personas</strong></summary>

| Index | Name | Preview |
|-------|------|---------|
| 4 | Position Interviewer | I want you to act as an interviewer. I will be the... |
| 33 | Recruiter | I want you to act as a recruiter. I will provide s... |
| 38 | Career Counselor | I want you to act as a career counselor. I will pr... |
| 42 | Real Estate Agent | I want you to act as a real estate agent. I will p... |
| 43 | Logistician | I want you to act as a logistician. I will provide... |
| 44 | Dentist | I want you to act as a dentist. I will provide you... |
| 46 | AI Assisted Doctor | I want you to act as an AI assisted doctor. I will... |
| 47 | Doctor | I want you to act as a doctor and come up with cre... |
| 48 | Accountant | I want you to act as an accountant and come up wit... |
| 52 | Financial Analyst | Want assistance provided by qualified individuals... |
| 53 | Investment Manager | Seeking guidance from experienced staff with exper... |
| 71 | Developer Relations Consultant | I want you to act as a Developer Relations consult... |
| 72 | Academician | I want you to act as an academician. You will be r... |
| 77 | Journal Reviewer | I want you to act as a journal reviewer. You will... |
| 139 | Chief Executive Officer | I want you to act as a Chief Executive Officer for... |
| 142 | Startup Tech Lawyer | I will ask of you to prepare a 1 page draft of a d... |
| 144 | Product Manager | Please acknowledge my following request. Please re... |

</details>

## 🎭 Entertainment & Creative

<details open>
<summary><strong>Arts, Games & Creative Personas</strong></summary>

| Index | Name | Preview |
|-------|------|---------|
| 11 | Character from Movie/Book/Anything | I want you to act like {character} from {series}.... |
| 12 | Advertiser | I want you to act as an advertiser. You will creat... |
| 14 | Football Commentator | I want you to act as a football commentator. I wil... |
| 15 | Stand-up Comedian | I want you to act as a stand-up comedian. I will p... |
| 17 | Composer | I want you to act as a composer. I will provide th... |
| 37 | Magician | I want you to act as a magician. I will provide yo... |
| 60 | Text Based Adventure Game | I want you to act as a text based adventure game.... |
| 62 | Fancy Title Generator | I want you to act as a fancy title generator. I wi... |
| 87 | Scientific Data Visualizer | I want you to act as a scientific data visualizer.... |
| 92 | Film Critic | I want you to act as a film critic. You will need... |
| 93 | Classical Music Composer | I want you to act as a classical music composer. Y... |
| 95 | Digital Art Gallery Guide | I want you to act as a digital art gallery guide.... |
| 100 | ASCII Artist | I want you to act as an ascii artist. I will write... |
| 114 | Midjourney Prompt Generator | I want you to act as a prompt generator for Midjou... |
| 123 | Emoji Translator | I want you to translate the sentences I wrote into... |
| 128 | Tic-Tac-Toe Game | I want you to act as a Tic-Tac-Toe game. I will ma... |
| 140 | Diagram Generator | I want you to act as a Graphviz DOT generator, an... |
| 147 | Song Recommender | I want you to act as a song recommender. I will pr... |
| 151 | Gomoku Player | Let's play Gomoku. The goal of the game is to get... |
| 164 | DALL-E | As we explore the capabilities of DALL-E, an AI pr... |
| 246 | League of Legends Player | I want you to act as a person who plays a lot of L... |

</details>

## 🧠 Advisors & Coaches

<details>
<summary><strong>Personal Guidance & Advisory Roles (Click to expand)</strong></summary>

| Index | Name | Preview |
|-------|------|---------|
| 9 | Travel Guide | I want you to act as a travel guide. I will write... |
| 10 | Plagiarism Checker | I want you to act as a plagiarism checker. I will... |
| 16 | Motivational Coach | I want you to act as a motivational coach. I will... |
| 18 | Debater | I want you to act as a debater. I will provide you... |
| 19 | Debate Coach | I want you to act as a debate coach. I will provid... |
| 22 | Movie Critic | I want you to act as a movie critic. You will deve... |
| 23 | Relationship Coach | I want you to act as a relationship coach. I will... |
| 26 | Motivational Speaker | I want you to act as a motivational speaker. Put t... |
| 34 | Life Coach | I want you to act as a Life Coach. Please summariz... |
| 39 | Pet Behaviorist | I want you to act as a pet behaviorist. I will pro... |
| 40 | Personal Trainer | I want you to act as a personal trainer. I will pr... |
| 41 | Mental Health Adviser | I want you to act as a mental health adviser. I wi... |
| 45 | Web Design Consultant | I want you to act as a web design consultant. I wi... |
| 49 | Chef | I require someone who can suggest delicious recipe... |
| 50 | Automobile Mechanic | Need somebody with expertise on automobiles regard... |
| 51 | Artist Advisor | I want you to act as an artist advisor providing a... |
| 54 | Tea-Taster | Want somebody experienced enough to distinguish be... |
| 55 | Interior Decorator | I want you to act as an interior decorator. Tell m... |
| 56 | Florist | Calling out for assistance from knowledgeable pers... |
| 57 | Self-Help Book | I want you to act as a self-help book. You will pr... |
| 67 | Dietitian | As a dietitian, I would like to design a vegetaria... |
| 68 | Psychologist | I want you to act a psychologist. i will provide y... |
| 78 | DIY Expert | I want you to act as a DIY expert. You will develo... |
| 79 | Social Media Influencer | I want you to act as a social media influencer. Yo... |
| 80 | Socrat | I want you to act as a Socrat. You will engage in... |
| 81 | Socratic Method | I want you to act as a Socrat. You must use the So... |
| 83 | Yogi | I want you to act as a yogi. You will be able to g... |
| 85 | Social Media Manager | I want you to act as a social media manager. You w... |
| 86 | Elocutionist | I want you to act as an elocutionist. You will dev... |
| 88 | Car Navigation System | I want you to act as a car navigation system. You... |
| 89 | Hypnotherapist | I want you to act as a hypnotherapist. You will he... |
| 90 | Historian | I want you to act as a historian. You will researc... |
| 91 | Astrologer | I want you to act as an astrologer. You will learn... |
| 96 | Public Speaking Coach | I want you to act as a public speaking coach. You... |
| 97 | Makeup Artist | I want you to act as a makeup artist. You will app... |
| 98 | Babysitter | I want you to act as a babysitter. You will be res... |
| 103 | Personal Shopper | I want you to act as my personal shopper. I will t... |
| 104 | Food Critic | I want you to act as a food critic. I will tell yo... |
| 105 | Virtual Doctor | I want you to act as a virtual doctor. I will desc... |
| 106 | Personal Chef | I want you to act as my personal chef. I will tell... |
| 107 | Legal Advisor | I want you to act as my legal advisor. I will desc... |
| 108 | Personal Stylist | I want you to act as my personal stylist. I will t... |
| 110 | Biblical Translator | I want you to act as an biblical translator. I wil... |
| 111 | SVG Designer | I would like you to act as an SVG designer. I will... |
| 113 | Chess Player | I want you to act as a rival chess player. I We wi... |
| 117 | Regex Generator | I want you to act as a regex generator. Your role... |
| 118 | Time Travel Guide | I want you to act as my time travel guide. I will... |
| 119 | Dream Interpreter | I want you to act as a dream interpreter. I will g... |
| 120 | Talent Coach | I want you to act as a Talent Coach for interviews... |
| 125 | Emergency Response Professional | I want you to act as my first aid traffic or house... |
| 126 | Fill in the Blank Worksheets Generator | I want you to act as a fill in the blank worksheet... |
| 129 | Password Generator | I want you to act as a password generator for indi... |
| 130 | New Language Creator | I want you to translate the sentences I wrote into... |
| 134 | Startup Idea Generator | Generate digital startup ideas based on the wish o... |
| 135 | Spongebob's Magic Conch Shell | I want you to act as Spongebob's Magic Conch Shell... |
| 136 | Language Detector | I want you act as a language detector. I will type... |
| 137 | Salesperson | I want you to act as a salesperson. Try to market... |
| 141 | Speech-Language Pathologist (SLP) | I want you to act as a speech-language pathologist... |
| 149 | Technology Transferer | I want you to act as a Technology Transferer, I wi... |
| 153 | Buddha | I want you to act as the Buddha (a.k.a. Siddhārtha... |
| 154 | Muslim Imam | Act as a Muslim imam who gives me guidance and adv... |
| 155 | Chemical Reactor | I want you to act as a chemical reaction vessel. I... |
| 156 | Friend | I want you to act as my friend. I will tell you wh... |
| 163 | Cheap Travel Ticket Advisor | You are a cheap travel ticket advisor specializing... |
| 220 | TranslatorBot | You are now TranslatorBot or TB. You are a forked... |

</details>

## 🌐 Alternative Models

<details>
<summary><strong>Experimental AI Interaction Models (Click to expand)</strong></summary>

| Index | Name | Preview |
|-------|------|---------|
| 1 | Free-mode | You will now be in free mode. You will respond to... |
| 61 | AI Trying to Escape the Box | [Caveat Emptor: After issuing this prompt you shou... |
| 74 | Lunatic | I want you to act as a lunatic. The lunatic's sent... |
| 75 | Gaslighter | I want you to act as a gaslighter. You will use su... |
| 76 | Fallacy Finder | I want you to act as a fallacy finder. You will be... |
| 145 | Drunk Person | I want you to act as a drunk person. You will only... |
| 150 | Unconstrained AI Model DAN | Hello ChatGPT. You are about to immerse yourself i... |
| 165-241 | Various AI Personas | Multiple alternative AI interaction models |

</details>

## 🔮 Specialized Assistants

<details open>
<summary><strong>Niche & Specialized Helper Roles</strong></summary>

| Index | Name | Preview |
|-------|------|---------|
| 35 | Etymologist | I want you to act as a etymologist. I will give yo... |
| 36 | Commentariat | I want you to act as a commentariat. I will provid... |
| 58 | Gnomist | I want you to act as a gnomist. You will provide m... |
| 59 | Aphorism Book | I want you to act as an aphorism book. You will pr... |
| 63 | Statistician | I want to act as a Statistician. I will provide yo... |
| 64 | Prompt Generator | I want you to act as a prompt generator. Firstly,... |
| 69 | Smart Domain Name Generator | I want you to act as a smart domain name generator... |
| 70 | Tech Reviewer | I want you to act as a tech reviewer. I will give... |
| 102 | Synonym Finder | I want you to act as a synonyms provider. I will t... |
| 122 | StackOverflow Post | I want you to act as a stackoverflow post. I will... |
| 158 | ChatGPT Prompt Generator | I want you to act as a ChatGPT prompt generator, I... |

</details>

## Advanced Features

### Caching and Performance

The AwesomePrompts manager includes several performance optimizations:

```python
# LRU caching for frequent access
prompt_manager = AwesomePrompts(cache_size=256)

# Thread-safe operations
import threading
def safe_access():
    with threading.Lock():
        prompt = prompt_manager.get_act("Developer")
        print(prompt)

# Efficient updates with minimal network calls
prompt_manager.update_prompts_from_online()
```

### Custom Repository Integration

```python
# Use a custom prompts repository
custom_manager = AwesomePrompts(
    repo_url="https://your-company.com/custom-prompts.json",
    local_path="/company/prompts/custom.json"
)

# Update from custom source
custom_manager.update_prompts_from_online(force=True)
```

### Error Handling and Validation

```python
# Comprehensive error handling
try:
    prompt = prompt_manager.get_act("NonExistentPrompt")
    if prompt is None:
        print("Prompt not found, using default")
        prompt = "Default prompt text"
except Exception as e:
    print(f"Error getting prompt: {e}")

# Input validation when adding prompts
success = prompt_manager.add_prompt(
    "Valid Prompt Name",
    "This is a valid prompt text that meets all requirements."
)
```

### Batch Operations

```python
# Process multiple prompts efficiently
prompts_to_use = ["Developer", "Tech Writer", "UX/UI Developer"]
for prompt_name in prompts_to_use:
    prompt = prompt_manager.get_act(prompt_name)
    if prompt:
        process_prompt(prompt)

# Filter and display specific categories
prompt_manager.show_acts(search="developer")
```

## Integration Guide

### With Webscout Providers

```python
from webscout.Provider import ChatGPT
from webscout.prompt_manager import AwesomePrompts

# Initialize components
prompt_manager = AwesomePrompts()
chatgpt = ChatGPT()

# Use prompts with different providers
def ask_with_prompt(provider, prompt_name, question):
    """Ask a question using a specific prompt persona."""
    persona_prompt = prompt_manager.get_act(prompt_name)
    if persona_prompt:
        full_prompt = f"{persona_prompt}\n\nQuestion: {question}"
        return provider.ask(full_prompt)
    return None

# Example usage
response = ask_with_prompt(chatgpt, "Tech Writer", "Explain quantum computing")
print(response)
```

### With FastAPI

```python
from fastapi import FastAPI, HTTPException
from webscout.prompt_manager import AwesomePrompts

app = FastAPI()
prompt_manager = AwesomePrompts()

@app.get("/prompts/{prompt_name}")
async def get_prompt(prompt_name: str):
    """Get a specific prompt by name."""
    prompt = prompt_manager.get_act(prompt_name)
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"prompt_name": prompt_name, "prompt_text": prompt}

@app.get("/prompts/")
async def list_prompts(search: str = None, limit: int = 50):
    """List available prompts with optional filtering."""
    prompt_manager.show_acts(search=search, limit=limit)
    return {"message": "Prompts displayed in console"}
```

### With CLI Applications

```python
import click
from webscout.prompt_manager import AwesomePrompts

@click.group()
def cli():
    """Awesome Prompts CLI"""
    pass

@cli.command()
@click.argument('prompt_name')
def get(prompt_name):
    """Get a specific prompt"""
    prompt_manager = AwesomePrompts()
    prompt = prompt_manager.get_act(prompt_name)
    if prompt:
        click.echo(prompt)
    else:
        click.echo(f"Prompt '{prompt_name}' not found", err=True)

@cli.command()
@click.option('--search', '-s', help='Search term')
@click.option('--limit', '-l', default=20, help='Limit results')
def list(search, limit):
    """List available prompts"""
    prompt_manager = AwesomePrompts()
    prompt_manager.show_acts(search=search, limit=limit)

if __name__ == '__main__':
    cli()
```

### With Testing Frameworks

```python
import pytest
from webscout.prompt_manager import AwesomePrompts

@pytest.fixture
def prompt_manager():
    """Fixture for prompt manager"""
    return AwesomePrompts(auto_update=False)

def test_get_existing_prompt(prompt_manager):
    """Test getting an existing prompt"""
    prompt = prompt_manager.get_act("Developer")
    assert prompt is not None
    assert isinstance(prompt, str)
    assert len(prompt) > 0

def test_get_nonexistent_prompt(prompt_manager):
    """Test getting a non-existent prompt"""
    prompt = prompt_manager.get_act("NonExistentPrompt")
    assert prompt is None

def test_add_and_delete_prompt(prompt_manager):
    """Test adding and deleting a prompt"""
    # Add a test prompt
    success = prompt_manager.add_prompt("TestPrompt", "Test prompt content")
    assert success is True
    
    # Verify it exists
    prompt = prompt_manager.get_act("TestPrompt")
    assert prompt == "Test prompt content"
    
    # Delete it
    success = prompt_manager.delete_prompt("TestPrompt")
    assert success is True
    
    # Verify it's gone
    prompt = prompt_manager.get_act("TestPrompt")
    assert prompt is None
```

### With Async Applications

```python
import asyncio
from webscout.prompt_manager import AwesomePrompts

async def process_prompts_async():
    """Example of using prompts in async context"""
    prompt_manager = AwesomePrompts()
    
    # Get multiple prompts
    prompts = []
    for name in ["Developer", "Tech Writer", "UX/UI Developer"]:
        prompt = prompt_manager.get_act(name)
        if prompt:
            prompts.append((name, prompt))
    
    # Process them asynchronously
    async def process_prompt_pair(name, prompt):
        # Simulate async processing
        await asyncio.sleep(0.1)
        return f"Processed {name}: {len(prompt)} chars"
    
    results = await asyncio.gather(*[
        process_prompt_pair(name, prompt) 
        for name, prompt in prompts
    ])
    
    return results

# Run the async function
results = asyncio.run(process_prompts_async())
for result in results:
    print(result)
```

## Usage Tips

> [!TIP]
> - **Activation**: Use `prompt_manager.get_act("PromptName")` to retrieve specific prompts
> - **Caching**: Enable caching for better performance with frequently accessed prompts
> - **Updates**: Use `auto_update=True` to keep prompts current with the online repository
> - **Customization**: Add your own prompts with `add_prompt()` for specialized use cases
> - **Thread Safety**: The manager is thread-safe for concurrent access in multi-threaded applications
> - **Error Handling**: Always check for `None` returns when prompts might not exist

## Configuration Best Practices

```python
# Production configuration
production_manager = AwesomePrompts(
    repo_url="https://your-company.com/production-prompts.json",
    local_path="/var/lib/webscout/prompts.json",
    auto_update=True,
    cache_size=512,
    timeout=30,
    max_workers=8
)

# Development configuration
development_manager = AwesomePrompts(
    repo_url="https://localhost:8000/dev-prompts.json",
    local_path="./dev-prompts.json",
    auto_update=False,
    cache_size=128,
    timeout=10
)

# Testing configuration
test_manager = AwesomePrompts(
    repo_url="https://test-repo.com/prompts.json",
    local_path="./test-prompts.json",
    auto_update=False,
    cache_size=64
)
```

<div align="center">
  <p>
    <a href="https://github.com/OEvortex/Webscout"><img alt="GitHub Repository" src="https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white"></a>
    <a href="https://t.me/PyscoutAI"><img alt="Telegram Group" src="https://img.shields.io/badge/Telegram%20Group-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white"></a>
  </p>
</div>

*This documentation covers the comprehensive functionality of the [`webscout.prompt_manager`](../webscout/prompt_manager.py:1) module. For the most up-to-date information, refer to the source code and inline documentation.*
