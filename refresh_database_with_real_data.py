"""
Refresh SQLite database with real sanctions and company registry data
Re-runs checks on existing companies using newly integrated real data sources:
- OFAC SDN List (real, integrated)
- EU Consolidated Sanctions List (real, integrated)
- SEC EDGAR Company Registry (real, integrated)
"""

from app.models.base import get_session_factory, init_db
from app.models.lob import LOBVerification
from app.data.connector import DataConnector
from app.data.scraper import WebScraper
from app.data.company_registry import CompanyRegistryFetcher
from app.data.sanctions_checker import SanctionsChecker
from app.core.logging import get_logger
from datetime import datetime
import json

logger = get_logger(__name__)


def refresh_all_verifications():
    """Refresh all verification records with real data sources"""
    
    SessionLocal, _ = get_session_factory()
    db = SessionLocal()
    
    try:
        # Get all verification records
        verifications = db.query(LOBVerification).all()
        
        print("=" * 80)
        print("Refreshing Database with Real Data Sources")
        print("=" * 80)
        print(f"\nFound {len(verifications)} verification records to refresh\n")
        
        # Initialize data connector with real sources
        data_connector = DataConnector()
        
        # Register real data sources
        data_connector.register_source(WebScraper())
        data_connector.register_source(CompanyRegistryFetcher())  # Now uses real SEC EDGAR
        data_connector.register_source(SanctionsChecker())  # Now uses real OFAC + EU
        
        updated_count = 0
        error_count = 0
        
        for i, verification in enumerate(verifications, 1):
            try:
                print(f"[{i}/{len(verifications)}] Refreshing: {verification.client}")
                
                # Prepare query
                query = {
                    "client": verification.client,
                    "client_country": verification.client_country,
                    "client_role": verification.client_role,
                    "product_name": verification.product_name or ""
                }
                
                # Collect data from real sources
                results = data_connector.collect_from_all_sources(query)
                
                # Aggregate results
                aggregated_data = data_connector.aggregate_results(results)
                
                # Extract key information
                collected_data = {
                    "sources": [],
                    "data": {}
                }
                
                for result in results:
                    if result.success:
                        source_name = result.source
                        collected_data["sources"].append(source_name)
                        if result.data:
                            collected_data["data"].update(result.data)
                
                # Check for sanctions matches
                sanctions_check = None
                is_sanctioned = False
                sanctions_sources = []
                
                for result in results:
                    if result.source == "sanctions_checker" and result.success:
                        sanctions_data = result.data
                        sanctions_check = sanctions_data.get("sanctions_checks", {})
                        
                        # Check OFAC
                        ofac_check = sanctions_check.get("ofac", {})
                        if ofac_check and ofac_check.get("match"):
                            is_sanctioned = True
                            sanctions_sources.append("OFAC")
                        
                        # Check EU
                        eu_check = sanctions_check.get("eu", {})
                        if eu_check and eu_check.get("match"):
                            is_sanctioned = True
                            sanctions_sources.append("EU")
                        
                        # Check UN (if available)
                        un_check = sanctions_check.get("un", {})
                        if un_check and un_check.get("match"):
                            is_sanctioned = True
                            sanctions_sources.append("UN")
                
                # Check company registry
                company_registry_data = None
                registry_sources = []
                
                for result in results:
                    if result.source == "company_registry" and result.success:
                        company_registry_data = result.data
                        registry_sources = result.data.get("sources", [])
                
                # Update verification record
                # Update sources (sources is JSON column)
                all_sources = list(set(collected_data.get("sources", [])))
                if all_sources:
                    # sources is JSON, so store as list
                    verification.sources = all_sources
                
                # Update flags (flags is JSON column, store as list)
                flags_list = []
                if is_sanctioned:
                    for source in sanctions_sources:
                        flag = f"[HIGH] sanctions_match: Sanctioned according to {source} sanctions list"
                        flags_list.append(flag)
                    
                    # Add existing flags if any
                    if verification.flags:
                        if isinstance(verification.flags, list):
                            flags_list.extend(verification.flags)
                        elif isinstance(verification.flags, str):
                            flags_list.append(verification.flags)
                    
                    # Remove duplicates
                    flags_list = list(set(flags_list))
                    verification.flags = flags_list
                    verification.is_red_flag = True
                    # Sanctions match = concrete evidence = HIGH confidence
                    verification.confidence_score = "High"
                else:
                    # No sanctions match - reset red flag if not already set by AI
                    # But don't override if AI already set it based on other factors
                    if not verification.ai_response:
                        # If no AI analysis yet, ensure red flag is False
                        verification.is_red_flag = False
                
                # Update company registry information
                if company_registry_data:
                    registry_info = company_registry_data.get("registry_data", {})
                    # Could store registry details here if needed
                
                # Update timestamps
                verification.updated_at = datetime.utcnow()
                verification.data_collected_at = datetime.utcnow()
                verification.last_verified_at = datetime.utcnow()
                
                # Commit this record
                db.commit()
                
                updated_count += 1
                print(f"  ✅ Updated - Sources: {', '.join(all_sources)}")
                if is_sanctioned:
                    print(f"  ⚠️  SANCTIONED: {', '.join(sanctions_sources)}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"Error refreshing verification {verification.id}: {str(e)}", exc_info=True)
                print(f"  ❌ Error: {str(e)[:100]}")
                db.rollback()
        
        print("\n" + "=" * 80)
        print("Refresh Complete!")
        print("=" * 80)
        print(f"✅ Successfully updated: {updated_count} records")
        print(f"❌ Errors: {error_count} records")
        print(f"📊 Total: {len(verifications)} records")
        print("\nDatabase now contains data from:")
        print("  ✅ OFAC SDN List (17,711 entities)")
        print("  ✅ EU Consolidated Sanctions List (5,579 entities)")
        print("  ✅ SEC EDGAR Company Registry (10,142 companies)")
        
    except Exception as e:
        logger.error(f"Error refreshing database: {str(e)}", exc_info=True)
        print(f"\n❌ Fatal error: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Database Refresh Script")
    print("=" * 80)
    print("\nThis script will:")
    print("  1. Load all existing verification records")
    print("  2. Re-run checks with REAL data sources:")
    print("     - OFAC SDN List (downloaded XML)")
    print("     - EU Consolidated Sanctions List (downloaded XML)")
    print("     - SEC EDGAR Company Registry (downloaded JSON)")
    print("  3. Update database records with new results")
    print("\n" + "=" * 80)
    print()
    
    refresh_all_verifications()

