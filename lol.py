from rich import print

from webscout.search.engines import (
    BraveImages,
    BraveNews,
    BraveSuggestions,
    BraveTextSearch,
    BraveVideos,
)


def main() -> None:
    # Test BraveImages
    print("[bold cyan]Testing BraveImages...[/bold cyan]")
    engine = BraveImages()
    results = engine.run("nature", max_results=1)
    print(results)
    print()

    # Test BraveTextSearch
    print("[bold cyan]Testing BraveTextSearch...[/bold cyan]")
    text_engine = BraveTextSearch()
    results2 = text_engine.run("artificial intelligence", max_results=5)
    print(results2)
    print()

    # Test BraveVideos
    print("[bold cyan]Testing BraveVideos...[/bold cyan]")
    videos_engine = BraveVideos()
    video_results = videos_engine.run("python tutorial", max_results=3)
    for i, video in enumerate(video_results, 1):
        print(f"[yellow]{i}.[/yellow] {video.title}")
        print(f"   URL: {video.url}")
        print(f"   Duration: {video.duration}")
        print(f"   Channel: {video.uploader}")
        print()

    # Test BraveNews
    print("[bold cyan]Testing BraveNews...[/bold cyan]")
    news_engine = BraveNews()
    news_results = news_engine.run("technology", max_results=3)
    for i, article in enumerate(news_results, 1):
        print(f"[yellow]{i}.[/yellow] {article.title}")
        print(f"   Source: {article.source}")
        print(f"   Date: {article.date}")
        print()

    # Test BraveSuggestions
    print("[bold cyan]Testing BraveSuggestions...[/bold cyan]")
    suggestions_engine = BraveSuggestions()
    suggestions = suggestions_engine.run("pyth", max_results=5)
    print("[bold]Suggestions for 'pyth':[/bold]")
    for i, suggestion in enumerate(suggestions, 1):
        if suggestion.is_entity:
            print(f"[yellow]{i}.[/yellow] [green]{suggestion.query}[/green] (Entity)")
            print(f"   {suggestion.desc}")
        else:
            print(f"[yellow]{i}.[/yellow] {suggestion.query}")
    print()


if __name__ == "__main__":
    main()
