"""
Test script for real company data collection
Scrapes company websites and stores data in database
"""

import sys
from datetime import datetime
from typing import List, Dict, Any

from app.data.connector import DataConnector
from app.data.scraper import WebScraper
from app.data.company_registry import CompanyRegistryFetcher
from app.data.sanctions_checker import SanctionsChecker
from app.data.validator import DataValidator
from app.data.storage import DataStorage
from app.data.freshness import DataFreshnessTracker
from app.data.url_finder import URLFinder
from app.core.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


class CompanyTester:
    """Test company data collection with real companies"""
    
    def __init__(self):
        """Initialize company tester"""
        self.connector = DataConnector()
        self.validator = DataValidator()
        self.storage = DataStorage()
        self.freshness_tracker = DataFreshnessTracker()
        self.url_finder = URLFinder()
        
        # Register data sources
        self.scraper = WebScraper(name="web_scraper", rate_limit=10)
        self.registry = CompanyRegistryFetcher(name="company_registry", rate_limit=5)
        self.sanctions = SanctionsChecker(name="sanctions_checker", rate_limit=10)
        
        self.connector.register_source(self.scraper)
        self.connector.register_source(self.registry)
        self.connector.register_source(self.sanctions)
        
        print("✓ Data sources registered:")
        print(f"  - {self.scraper.name}")
        print(f"  - {self.registry.name}")
        print(f"  - {self.sanctions.name}")
        print(f"  - {self.url_finder.__class__.__name__}")
    
    def process_company(
        self,
        company_name: str,
        country: str = "US",
        role: str = "Export",
        product: str = "General",
        company_url: str = None
    ) -> Dict[str, Any]:
        """
        Process a single company
        
        Args:
            company_name: Name of the company
            country: Country code (default: US)
            role: Import/Export role (default: Export)
            product: Product name (default: General)
            company_url: Optional direct URL to company website
        
        Returns:
            Dictionary with processing results
        """
        print(f"\n{'='*60}")
        print(f"Processing: {company_name}")
        print(f"Country: {country}, Role: {role}, Product: {product}")
        if company_url:
            print(f"URL: {company_url}")
        print(f"{'='*60}")
        
        # Prepare query
        query = {
            "client": company_name,
            "client_country": country,
            "client_role": role,
            "product_name": product,
            "url": company_url  # If URL provided, scrape it directly
        }
        
        results = {}
        
        try:
            # Collect data from all sources
            print("\n📡 Collecting data from sources...")
            collection_results = self.connector.collect_from_all_sources(query)
            
            successful_sources = [r for r in collection_results if r.success]
            print(f"✓ Collected from {len(successful_sources)}/{len(collection_results)} sources")
            
            # Validate and clean data
            print("\n🧹 Validating and cleaning data...")
            cleaned_results = []
            for result in collection_results:
                if result.success and result.data:
                    cleaned = self.validator.validate_and_clean(
                        result.data,
                        result.source
                    )
                    cleaned_results.append(cleaned)
            
            # Merge data
            print("\n📊 Aggregating data...")
            aggregated_data = self.validator.merge_data(cleaned_results)
            
            print(f"✓ Aggregated data from {len(aggregated_data.get('sources', []))} sources")
            
            # Store in database
            print("\n💾 Storing in database...")
            input_data = {
                "client": company_name,
                "client_country": country,
                "client_role": role,
                "product_name": product
            }
            
            collected_at = datetime.utcnow()
            freshness_score = self.freshness_tracker.calculate_freshness_score(collected_at)
            
            verification_id = self.storage.store_verification(
                input_data,
                {"sources": [r.source for r in collection_results if r.success]},
                aggregated_data
            )
            
            if verification_id:
                # Update with freshness tracking
                self.storage.update_verification(verification_id, {
                    "data_collected_at": collected_at,
                    "data_freshness_score": freshness_score,
                    "last_verified_at": collected_at,
                    "website_source": aggregated_data.get("data", {}).get("url")
                })
                
                # Track sources
                for result in collection_results:
                    if result.success and result.data:
                        source_url = result.data.get("sources", [{}])[0].get("url") if result.source == "web_scraper" else None
                        self.storage.track_data_source(
                            verification_id,
                            result.source,
                            source_url,
                            collected_at
                        )
                
                print(f"✅ Stored successfully: ID={verification_id}")
                
                # Retrieve and display summary
                verification = self.storage.get_verification(verification_id)
                
                results = {
                    "success": True,
                    "verification_id": verification_id,
                    "sources_count": len(aggregated_data.get("sources", [])),
                    "data": aggregated_data,
                    "verification": verification
                }
                
                # Display summary
                print(f"\n📋 Summary:")
                print(f"  - Verification ID: {verification_id}")
                print(f"  - Sources: {len(aggregated_data.get('sources', []))}")
                print(f"  - Freshness: {freshness_score}")
                if verification:
                    print(f"  - Created: {verification.get('created_at')}")
                
            else:
                print("❌ Failed to store verification")
                results = {"success": False, "error": "Storage failed"}
        
        except Exception as e:
            logger.error(f"Error processing company {company_name}", error=str(e), exc_info=True)
            print(f"❌ Error processing company: {e}")
            results = {"success": False, "error": str(e)}
        
        return results
    
    def process_companies(
        self,
        companies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process multiple companies
        
        Args:
            companies: List of company dictionaries with:
                - name: Company name (required)
                - country: Country code (optional, default: US)
                - role: Import/Export (optional, default: Export)
                - product: Product name (optional, default: General)
                - url: Optional company website URL
        
        Returns:
            List of processing results
        """
        results = []
        
        print(f"\n{'='*60}")
        print(f"Processing {len(companies)} companies")
        print(f"{'='*60}\n")
        
        for i, company in enumerate(companies, 1):
            print(f"\n[{i}/{len(companies)}] Processing...")
            
            result = self.process_company(
                company_name=company.get("name", ""),
                country=company.get("country", "US"),
                role=company.get("role", "Export"),
                product=company.get("product", "General"),
                company_url=company.get("url")
            )
            
            results.append(result)
            
            # Small delay between companies to respect rate limits
            import time
            if i < len(companies):
                time.sleep(2)  # 2 second delay between companies
        
        return results


def main():
    """Main function"""
    print("="*60)
    print("Company Data Collection Tester")
    print("="*60)
    print()
    
    tester = CompanyTester()
    
    # Example companies - user can replace this with their list
    print("\n📝 Example companies list:")
    print("You can modify the companies list in the script or provide via command line")
    print()
    
    # Company list provided by user
    # URLs will be discovered automatically by URLFinder
    companies = [
        {"name": "Vitol Group", "country": "NL", "role": "Export", "product": "Energy Trading"},
        {"name": "Trafigura Group", "country": "SG", "role": "Export", "product": "Commodity Trading"},
        {"name": "Glencore", "country": "CH", "role": "Export", "product": "Commodity Trading"},
        {"name": "Gunvor Group", "country": "CH", "role": "Export", "product": "Energy Trading"},
        {"name": "Mercuria Energy Group", "country": "CH", "role": "Export", "product": "Energy Trading"},
        {"name": "Koch Industries", "country": "US", "role": "Export", "product": "Energy & Chemicals"},
        {"name": "ExxonMobil", "country": "US", "role": "Export", "product": "Oil & Gas"},
        {"name": "Shell plc", "country": "GB", "role": "Export", "product": "Oil & Gas"},
        {"name": "BP (British Petroleum)", "country": "GB", "role": "Export", "product": "Oil & Gas"},
        {"name": "TotalEnergies", "country": "FR", "role": "Export", "product": "Oil & Gas"},
        {"name": "Chevron", "country": "US", "role": "Export", "product": "Oil & Gas"},
        {"name": "Eni", "country": "IT", "role": "Export", "product": "Oil & Gas"},
        {"name": "ConocoPhillips", "country": "US", "role": "Export", "product": "Oil & Gas"},
        {"name": "Rosneft Oil Company", "country": "RU", "role": "Export", "product": "Oil & Gas"},
        {"name": "Lukoil OAO", "country": "RU", "role": "Export", "product": "Oil & Gas"},
        {"name": "Gazprom Neft", "country": "RU", "role": "Export", "product": "Oil & Gas"},
        {"name": "Surgutneftegas", "country": "RU", "role": "Export", "product": "Oil & Gas"}
    ]
    
    print("Current test companies:")
    for i, company in enumerate(companies, 1):
        print(f"  {i}. {company['name']} ({company['country']})")
        if company.get('url'):
            print(f"     URL: {company['url']}")
    
    print("\n" + "="*60)
    print("Step 1: Finding Company URLs")
    print("="*60)
    
    # Find URLs for companies that don't have one
    url_finder = URLFinder()
    companies_with_urls = url_finder.batch_find_urls(companies, delay=1.0)
    
    print("\n" + "="*60)
    print("Step 2: Starting Data Collection")
    print("="*60)
    
    # Process companies (use companies with found URLs)
    results = tester.process_companies(companies_with_urls)
    
    # Summary
    print(f"\n{'='*60}")
    print("Processing Summary")
    print(f"{'='*60}")
    
    successful = sum(1 for r in results if r.get("success"))
    total = len(results)
    
    print(f"Total companies processed: {total}")
    print(f"Successfully stored: {successful}")
    print(f"Failed: {total - successful}")
    
    if successful > 0:
        print(f"\n✅ Stored verifications:")
        for result in results:
            if result.get("success"):
                print(f"  - ID {result.get('verification_id')}: {result.get('verification', {}).get('client', 'Unknown')}")
    
    print("\n" + "="*60)
    
    return 0 if successful == total else 1


if __name__ == "__main__":
    sys.exit(main())

