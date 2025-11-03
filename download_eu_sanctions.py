"""
Download EU Consolidated Sanctions List
EU sanctions are published in various formats - checking for downloadable files
"""

import requests
from pathlib import Path
import json

def check_eu_sanctions_sources():
    """Check available EU sanctions data sources"""
    
    headers = {
        "User-Agent": "TBAML-System Sanctions Verification",
        "Accept": "application/json, application/xml, text/xml, */*"
    }
    
    print("Checking EU Sanctions Data Sources...")
    print("=" * 80)
    
    # Known EU sanctions URLs
    urls_to_check = {
        "EU Sanctions Map": "https://www.sanctionsmap.eu/",
        "ECB Sanctions": "https://www.ecb.europa.eu/ecb/legal/html/index.en.html",
        "EUR-Lex Restrictive Measures": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014D0145",
        "EU Consolidated List (Council)": "https://www.consilium.europa.eu/en/policies/sanctions/restrictive-measures/",
        "EU Open Data Portal": "https://data.europa.eu/data/datasets?locale=en",
    }
    
    # Check if these sites exist and have downloadable data
    for name, url in urls_to_check.items():
        print(f"\n{name}:")
        print(f"  URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            print(f"  Status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            
            # Check if response contains keywords indicating downloadable files
            content = response.text.lower()
            keywords = ['download', 'xml', 'csv', 'export', 'consolidated', 'sanctions', 'restrictive']
            found_keywords = [kw for kw in keywords if kw in content]
            
            if found_keywords:
                print(f"  Keywords found: {', '.join(found_keywords)}")
        except Exception as e:
            print(f"  Error: {str(e)[:50]}")
    
    print("\n" + "=" * 80)
    print("\nNote: EU sanctions lists are typically available through:")
    print("1. EU Sanctions Map (web interface)")
    print("2. EUR-Lex (legal documents)")
    print("3. Council of the EU website (official decisions)")
    print("4. May require API integration or web scraping")
    print("\nEU sanctions are often published as:")
    print("- Legal documents (EUR-Lex)")
    print("- Web-based interfaces (Sanctions Map)")
    print("- May not have downloadable XML/CSV like OFAC")
    
    return None

def check_eu_api_endpoints():
    """Check if EU has public APIs for sanctions"""
    
    print("\n" + "=" * 80)
    print("Checking for EU Sanctions APIs...")
    print("=" * 80)
    
    # Common API endpoint patterns
    api_patterns = [
        "https://api.ec.europa.eu/sanctions",
        "https://api.europa.eu/sanctions",
        "https://data.europa.eu/api/sanctions",
        "https://www.sanctionsmap.eu/api",
    ]
    
    headers = {
        "User-Agent": "TBAML-System Sanctions Verification",
        "Accept": "application/json"
    }
    
    for url in api_patterns:
        print(f"\nChecking: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=5, allow_redirects=False)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print(f"  ✅ API endpoint found!")
        except Exception as e:
            print(f"  Status: {str(e)[:50]}")
    
    print("\n" + "=" * 80)
    print("\nConclusion:")
    print("EU sanctions data typically requires:")
    print("1. Web scraping from sanctionsmap.eu")
    print("2. API integration (if available)")
    print("3. Manual data extraction from EUR-Lex documents")
    print("4. Unlike OFAC, EU doesn't provide downloadable XML/CSV files directly")

if __name__ == "__main__":
    check_eu_sanctions_sources()
    check_eu_api_endpoints()

