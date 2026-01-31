# Search Queries

> **Last updated:** 2026-01-24  
> **Level:** Beginner  
> **Time to learn:** 5 minutes

Perform web searches using multiple search engines.

---

## What You'll Learn

- Search the web with different engines
- Parse and process search results
- Use advanced search options
- Combine search with AI analysis

---

## Table of Contents

1. [DuckDuckGo (Default)](#duckduckgo-default)
2. [Other Search Engines](#other-search-engines)
3. [Processing Results](#processing-results)
4. [Advanced Search](#advanced-search)
5. [Combining Search with AI](#combining-search-with-ai)

---

## DuckDuckGo (Default)

### Basic Text Search

```python
from webscout import DuckDuckGoSearch

# Create search engine
search = DuckDuckGoSearch()

# Search for something
results = search.text("python programming tips", max_results=5)

# Display results
for i, result in enumerate(results, 1):
    print(f"{i}. {result['title']}")
    print(f"   URL: {result['link']}")
    print(f"   Description: {result['body']}\n")
```

**Output:**
```
1. Python Tips and Tricks - Real Python
   URL: https://realpython.com/python-tips-tricks/
   Description: Learn useful Python tips and tricks to improve your coding...

2. 10 Python Programming Tips - Medium
   URL: https://medium.com/python-tips/
   Description: Discover 10 essential Python programming tips...
```

### Image Search

```python
from webscout import DuckDuckGoSearch

search = DuckDuckGoSearch()

# Search for images
results = search.images("mountain landscape", max_results=5)

for i, result in enumerate(results, 1):
    print(f"{i}. {result['title']}")
    print(f"   Image URL: {result['image']}")
    print(f"   Source: {result['source']}\n")
```

### Video Search

```python
from webscout import DuckDuckGoSearch

search = DuckDuckGoSearch()

# Search for videos
results = search.videos("python tutorial", max_results=3)

for i, result in enumerate(results, 1):
    print(f"{i}. {result.get('title', 'Video')}")
    print(f"   URL: {result.get('link', 'N/A')}")
    print(f"   Duration: {result.get('duration', 'N/A')}\n")
```

### News Search

```python
from webscout import DuckDuckGoSearch

search = DuckDuckGoSearch()

# Search for latest news
results = search.news("artificial intelligence", max_results=5)

for i, result in enumerate(results, 1):
    print(f"{i}. {result['title']}")
    print(f"   Published: {result.get('date', 'N/A')}")
    print(f"   Source: {result.get('source', 'N/A')}")
    print(f"   Description: {result['body']}\n")
```

---

## Other Search Engines

### Bing Search

```python
from webscout import BingSearch

search = BingSearch()

# Text search
results = search.text("machine learning", max_results=5)

for result in results:
    print(f"Title: {result['title']}")
    print(f"URL: {result['link']}")
    print(f"Description: {result['body']}\n")
```

### Yahoo Search

```python
from webscout import YahooSearch

search = YahooSearch()

# Yahoo search
results = search.text("web development", max_results=5)

for result in results:
    print(f"{result['title']} - {result['link']}")
```

### Yep Search (Privacy-Focused)

```python
from webscout import YepSearch

search = YepSearch()

# Yep search
results = search.text("privacy online", max_results=5)

for result in results:
    print(f"{result['title']}")
    print(f"URL: {result['link']}\n")
```

### Brave Search

```python
from webscout import BraveSearch

search = BraveSearch()

# Brave search
results = search.text("cybersecurity", max_results=5)

for result in results:
    print(f"{result['title']} ({result['link']})")
```

---

## Processing Results

### Extract Titles Only

```python
from webscout import DuckDuckGoSearch

search = DuckDuckGoSearch()
results = search.text("python", max_results=10)

titles = [r['title'] for r in results]
for i, title in enumerate(titles, 1):
    print(f"{i}. {title}")
```

### Extract URLs Only

```python
from webscout import DuckDuckGoSearch

search = DuckDuckGoSearch()
results = search.text("api design", max_results=5)

urls = [r['link'] for r in results]

# Save to file
with open("urls.txt", "w") as f:
    for url in urls:
        f.write(url + "\n")

print(f"Saved {len(urls)} URLs to urls.txt")
```

### Filter Results by Keyword

```python
from webscout import DuckDuckGoSearch

search = DuckDuckGoSearch()
results = search.text("python", max_results=20)

# Filter for official documentation
official_results = [
    r for r in results 
    if "python.org" in r['link'] or "docs.python.org" in r['link']
]

print(f"Found {len(official_results)} official Python docs")
for result in official_results:
    print(f"- {result['title']}")
    print(f"  {result['link']}")
```

### Group Results by Domain

```python
from webscout import DuckDuckGoSearch
from urllib.parse import urlparse

search = DuckDuckGoSearch()
results = search.text("web development", max_results=15)

# Group by domain
grouped = {}
for result in results:
    domain = urlparse(result['link']).netloc
    if domain not in grouped:
        grouped[domain] = []
    grouped[domain].append(result)

# Display grouped results
for domain, items in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n{domain} ({len(items)} results)")
    for item in items:
        print(f"  - {item['title']}")
```

---

## Advanced Search

### Search with Filters

```python
from webscout import DuckDuckGoSearch

search = DuckDuckGoSearch()

# Search with max results
results = search.text(
    "python tutorials",
    max_results=10,
    # Other parameters depend on the search engine
)

for result in results:
    print(f"{result['title']}")
    print(f"{result['link']}\n")
```

### Search Multiple Terms

```python
from webscout import DuckDuckGoSearch

search = DuckDuckGoSearch()

search_terms = [
    "python best practices",
    "python performance optimization",
    "python security",
]

all_results = {}

for term in search_terms:
    print(f"Searching: {term}")
    results = search.text(term, max_results=3)
    all_results[term] = results

# Display results grouped by search term
for term, results in all_results.items():
    print(f"\n=== Results for: {term} ===")
    for result in results:
        print(f"{result['title']}")
        print(f"{result['link']}\n")
```

### Wikipedia Search

```python
from webscout import Wikipedia

wiki = Wikipedia()

# Search Wikipedia
results = wiki.text("machine learning", max_results=1)

for result in results:
    print(f"Title: {result['title']}")
    print(f"Summary: {result['body'][:200]}...")
    print(f"URL: {result['link']}")
```

---

## Combining Search with AI

### Summarize Search Results with AI

```python
from webscout import DuckDuckGoSearch, Meta

def search_and_summarize(query: str) -> str:
    """Search web and summarize results with AI."""
    
    # Search the web
    search = DuckDuckGoSearch()
    results = search.text(query, max_results=3)
    
    # Combine results
    combined = f"Question: {query}\n\nSearch Results:\n"
    for i, result in enumerate(results, 1):
        combined += f"\n{i}. {result['title']}\n{result['body']}\n"
    
    # Summarize with AI
    ai = Meta()
    prompt = f"{combined}\n\nPlease summarize these results in 2-3 sentences."
    summary = ai.chat(prompt)
    
    return summary

# Use it
result = search_and_summarize("what is quantum computing")
print(result)
```

### Get Latest News and Analyze

```python
from webscout import DuckDuckGoSearch, GROQ

def get_news_summary(topic: str) -> str:
    """Get latest news and AI summary."""
    
    # Search for news
    search = DuckDuckGoSearch()
    news_results = search.news(topic, max_results=3)
    
    # Format news items
    news_text = f"Latest News about {topic}:\n\n"
    for i, item in enumerate(news_results, 1):
        news_text += f"{i}. {item['title']}\n"
        news_text += f"   Source: {item.get('source', 'N/A')}\n"
        news_text += f"   {item['body']}\n\n"
    
    # Analyze with AI
    client = GROQ(api_key="your-api-key")
    analysis = client.chat(
        f"{news_text}\nWhat are the key takeaways from this news?"
    )
    
    return analysis

# Use it
summary = get_news_summary("artificial intelligence")
print(summary)
```

### Real-Time Research Assistant

```python
from webscout import DuckDuckGoSearch, Meta

def research_assistant(query: str):
    """Research assistant that searches and answers questions."""
    
    print(f"Researching: {query}\n")
    print("=" * 60)
    
    # Search
    search = DuckDuckGoSearch()
    results = search.text(query, max_results=5)
    
    # Prepare context from results
    context = "Search Results:\n"
    for i, result in enumerate(results, 1):
        context += f"{i}. {result['title']}: {result['body'][:100]}...\n"
    
    # Get AI response
    ai = Meta()
    prompt = f"{context}\n\nBased on these search results, explain {query}"
    response = ai.chat(prompt)
    
    print(f"Answer:\n{response}\n")
    print("=" * 60)
    print(f"Sources:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['link']}")

# Use it
research_assistant("how does photosynthesis work")
```

---

## CLI Usage

### From Command Line

```bash
# DuckDuckGo text search
webscout text -k "python programming"

# Image search
webscout images -k "mountain landscape"

# News search
webscout news -k "technology news"

# Weather
webscout weather -l "New York"

# Using different search engine
webscout bing_text -k "machine learning"
webscout yahoo_text -k "web development"
```

### Save Search Results

```bash
# Using Python
python -c "
from webscout import DuckDuckGoSearch
import json

search = DuckDuckGoSearch()
results = search.text('python', max_results=10)

with open('results.json', 'w') as f:
    json.dump(results, f, indent=2)

print('Results saved to results.json')
"
```

---

## Real-World Example: Content Research Tool

```python
from webscout import DuckDuckGoSearch
import json
from datetime import datetime

class ContentResearcher:
    """Tool for researching content topics."""
    
    def __init__(self):
        self.search = DuckDuckGoSearch()
    
    def research_topic(self, topic: str, num_results: int = 10) -> dict:
        """Research a topic and return structured data."""
        
        results = self.search.text(topic, max_results=num_results)
        
        return {
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "total_results": len(results),
            "results": results,
            "domains": list(set(
                self._extract_domain(r['link']) for r in results
            ))
        }
    
    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        return urlparse(url).netloc
    
    def save_research(self, data: dict, filename: str = None):
        """Save research to JSON file."""
        if filename is None:
            filename = f"research_{data['topic']}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename

# Use the tool
researcher = ContentResearcher()
research = researcher.research_topic("machine learning applications", num_results=10)
filename = researcher.save_research(research)
print(f"Research saved to {filename}")
```

---

## See Also

- [Basic Chat Examples](basic-chat.md)
- [Combining Search with AI](#combining-search-with-ai)
- [Getting Started](../getting-started.md)
- [API Reference](../api-reference.md)

Next: Learn about [Text-to-Image Generation](text-to-image.md)
