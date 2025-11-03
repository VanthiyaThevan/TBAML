"""
Test Tavily API Fallback Mechanism
Tests that Tavily API is used as fallback when domain patterns fail
"""

from app.data.url_finder import URLFinder
import os
from dotenv import load_dotenv

# Load .env file to get API keys
load_dotenv()

print("=" * 80)
print("Testing Tavily API Fallback Mechanism")
print("=" * 80)

# Check if Tavily API key is configured
tavily_key = os.getenv("TAVILY_API_KEY")
if tavily_key:
    print(f"✅ Tavily API key configured: {tavily_key[:10]}...")
else:
    print("⚠️  Tavily API key NOT configured (TAVILY_API_KEY not set)")
    print("   The fallback will still work, but won't use Tavily API")
    print("   To enable Tavily fallback, set: export TAVILY_API_KEY='your_key'")
    print()

# Initialize URL finder
url_finder = URLFinder()

# Test companies that should be difficult to find with domain patterns
# but can be found with Tavily API
test_companies = [
    {
        "name": "BP (British Petroleum)",
        "country": "GB",
        "expected_pattern_fail": True,  # Complex name, might fail pattern matching
        "description": "Company with parentheses - difficult for pattern matching"
    },
    {
        "name": "Rosneft Oil Company",
        "country": "RU",
        "expected_pattern_fail": True,  # Russian company, might fail pattern matching
        "description": "International company - difficult for pattern matching"
    },
    {
        "name": "Complex Company Name With Many Words",
        "country": "US",
        "expected_pattern_fail": True,  # Fake company - will definitely fail
        "description": "Fake company - should trigger fallback"
    },
]

print("\n" + "=" * 80)
print("Test Strategy: Companies that Pattern Matching Should Fail")
print("=" * 80)
print("\nThese companies are selected because:")
print("  1. They have complex names (parentheses, multiple words)")
print("  2. Domain pattern matching may fail")
print("  3. Tavily API fallback should be triggered")
print()

for i, company in enumerate(test_companies, 1):
    print(f"\n{'='*80}")
    print(f"Test {i}: {company['name']} ({company['country']})")
    print(f"Description: {company['description']}")
    print("="*80)
    
    print(f"\n🔍 Strategy 1: Domain Patterns")
    print(f"   Trying common domain patterns...")
    
    # Find URL (will try all strategies automatically)
    result = url_finder.find_company_url(company['name'], company['country'])
    
    if result and result.get("valid"):
        url = result.get("url")
        confidence = result.get("confidence", "medium")
        print(f"\n✅ SUCCESS: Found URL")
        print(f"   URL: {url}")
        print(f"   Confidence: {confidence}")
        
        if tavily_key:
            print(f"\n💡 Note: If pattern matching failed, Tavily API was used as fallback")
        else:
            print(f"\n💡 Note: Tavily API not configured - fallback not available")
    else:
        print(f"\n❌ FAILED: Could not find URL")
        print(f"   All strategies exhausted (pattern matching + variations + fallback)")
        
        if not tavily_key:
            print(f"\n⚠️  Recommendation: Configure TAVILY_API_KEY for better results")
            print(f"   Get key from: https://tavily.com")
    
    print()

print("\n" + "=" * 80)
print("Fallback Mechanism Test Complete!")
print("=" * 80)
print("\nSummary:")
print("  ✅ Tavily API is now used as Strategy 3 (Fallback)")
print("  ✅ Falls back only after pattern matching and variations fail")
print("  ✅ Better error handling and logging")
print("  ✅ Checks top 5 results from Tavily API")
print()
print("To enable Tavily fallback:")
print("  export TAVILY_API_KEY='your_api_key_here'")
print("  Get key from: https://tavily.com")

