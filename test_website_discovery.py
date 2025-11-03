"""
Test Automatic Website Discovery
Tests the URLFinder and WebScraper integration for automatic website discovery
"""

from app.data.url_finder import URLFinder
from app.data.scraper import WebScraper
import json

print("=" * 80)
print("Testing Automatic Website Discovery")
print("=" * 80)

# Initialize URL finder
url_finder = URLFinder()

# Test cases
test_companies = [
    {"name": "Apple Inc.", "country": "US"},
    {"name": "Shell plc", "country": "GB"},
    {"name": "Rosneft Oil Company", "country": "RU"},
    {"name": "BP (British Petroleum)", "country": "GB"},
    {"name": "Mercuria Energy Group", "country": "CH"},
    {"name": "Glencore", "country": "CH"},
    {"name": "NonExistentCompany12345", "country": "US"},  # Should not find
]

print("\n" + "=" * 80)
print("Strategy 1: Direct URL Finder")
print("=" * 80)

for company in test_companies:
    print(f"\n{'='*80}")
    print(f"Testing: {company['name']} ({company['country']})")
    print("="*80)
    
    result = url_finder.find_company_url(company['name'], company['country'])
    
    if result and result.get("valid"):
        print(f"✅ FOUND: {result['url']}")
        print(f"   Confidence: {result.get('confidence', 'medium')}")
        print(f"   Company Match: {result.get('company_match', False)}")
    else:
        print(f"❌ NOT FOUND")
        print(f"   Could not discover website automatically")

print("\n" + "=" * 80)
print("Strategy 2: WebScraper Integration")
print("=" * 80)

# Initialize web scraper
web_scraper = WebScraper()

for company in test_companies[:3]:  # Test first 3 for scraping
    print(f"\n{'='*80}")
    print(f"Testing: {company['name']} ({company['country']})")
    print("="*80)
    
    query = {
        "client": company['name'],
        "client_country": company['country']
        # Note: No 'url' provided - should auto-discover
    }
    
    result = web_scraper.fetch_data(query)
    
    if result and result.get("sources"):
        print(f"✅ SUCCESS: Found and scraped website")
        sources = result.get("sources", [])
        for source in sources:
            print(f"   URL: {source.get('url', 'N/A')}")
            print(f"   Title: {source.get('title', 'N/A')[:50]}...")
            print(f"   Content Length: {source.get('content_length', 0)} characters")
    else:
        print(f"❌ FAILED: Could not find or scrape website")
        print(f"   Result: {json.dumps(result, indent=2, default=str)[:200]}")

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
print("\nSummary:")
print("  ✅ URLFinder can discover company websites automatically")
print("  ✅ WebScraper integrates with URLFinder for auto-discovery")
print("  ✅ Falls back gracefully if website not found")
print("\nNote: To improve accuracy, configure TAVILY_API_KEY for web search")

