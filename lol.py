from webscout.search.engines import BraveImages
from rich import print
# Create engine
engine = BraveImages()

# Search for images
results = engine.run("nature", max_results=10)
print(results)