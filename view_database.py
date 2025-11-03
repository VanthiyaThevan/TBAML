"""
View scraped company data from SQLite database
Displays all collected data from companies
"""

import json
from app.models.base import get_session_factory
from app.models.lob import LOBVerification
from datetime import datetime


def format_timestamp(ts):
    """Format timestamp for display"""
    if ts:
        if isinstance(ts, str):
            return ts
        return ts.strftime("%Y-%m-%d %H:%M:%S")
    return "N/A"


def view_all_companies():
    """View all companies in database"""
    SessionLocal, _ = get_session_factory()
    db = SessionLocal()
    
    try:
        verifications = db.query(LOBVerification).order_by(
            LOBVerification.created_at.desc()
        ).all()
        
        print("=" * 80)
        print("SCRAPED COMPANY DATA FROM SQLITE DATABASE")
        print("=" * 80)
        print(f"\nTotal Records: {len(verifications)}\n")
        
        for i, v in enumerate(verifications, 1):
            print(f"{'='*80}")
            print(f"Record #{i} - ID: {v.id}")
            print(f"{'='*80}")
            
            # Basic Info
            print("\n📋 Company Information:")
            print(f"  Company Name: {v.client}")
            print(f"  Country: {v.client_country}")
            print(f"  Role: {v.client_role}")
            print(f"  Product: {v.product_name}")
            
            # Website Data
            print("\n🌐 Website Data:")
            print(f"  Website URL: {v.website_source or 'Not found/Not scraped'}")
            print(f"  Publication Date: {v.publication_date or 'N/A'}")
            
            # Activity & Status
            print("\n📊 Analysis Results:")
            print(f"  Activity Level: {v.activity_level or 'Not analyzed yet'}")
            print(f"  Confidence Score: {v.confidence_score or 'N/A'}")
            print(f"  Red Flag: {'Yes' if v.is_red_flag else 'No'}")
            
            # Flags
            if v.flags:
                print(f"\n⚠️  Flags/Alerts:")
                if isinstance(v.flags, list):
                    for flag in v.flags:
                        print(f"    - {flag}")
                else:
                    print(f"    - {v.flags}")
            
            # AI Response
            if v.ai_response:
                print(f"\n🤖 AI Response:")
                # Truncate if too long
                ai_resp = v.ai_response[:500] + "..." if len(v.ai_response) > 500 else v.ai_response
                print(f"  {ai_resp}")
            
            # Data Sources
            print(f"\n📡 Data Sources ({len(v.sources) if v.sources else 0}):")
            if v.sources:
                if isinstance(v.sources, list):
                    for j, source in enumerate(v.sources, 1):
                        if isinstance(source, dict):
                            print(f"  {j}. {source.get('name', 'Unknown')}")
                            if source.get('url'):
                                print(f"     URL: {source.get('url')}")
                            if source.get('collected_at'):
                                print(f"     Collected: {source.get('collected_at')}")
                        else:
                            print(f"  {j}. {source}")
                else:
                    print(f"  {v.sources}")
            else:
                print("  No sources tracked")
            
            # Metadata
            print(f"\n📅 Timestamps:")
            print(f"  Created: {format_timestamp(v.created_at)}")
            print(f"  Updated: {format_timestamp(v.updated_at)}")
            print(f"  Data Collected: {format_timestamp(v.data_collected_at)}")
            print(f"  Last Verified: {format_timestamp(v.last_verified_at)}")
            print(f"  Freshness Score: {v.data_freshness_score or 'N/A'}")
            
            print()
        
        # Summary statistics
        print(f"\n{'='*80}")
        print("DATABASE STATISTICS")
        print(f"{'='*80}\n")
        
        # Count by country
        countries = {}
        for v in verifications:
            country = v.client_country
            countries[country] = countries.get(country, 0) + 1
        
        print("Companies by Country:")
        for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
            print(f"  {country}: {count}")
        
        # Count with URLs
        with_urls = sum(1 for v in verifications if v.website_source)
        print(f"\nCompanies with Website URLs: {with_urls}/{len(verifications)}")
        
        # Count with sources
        with_sources = sum(1 for v in verifications if v.sources and len(v.sources) > 0)
        print(f"Companies with Data Sources: {with_sources}/{len(verifications)}")
        
        # Count with AI analysis
        with_ai = sum(1 for v in verifications if v.ai_response)
        print(f"Companies with AI Analysis: {with_ai}/{len(verifications)}")
        
        # Red flags
        red_flags = sum(1 for v in verifications if v.is_red_flag)
        print(f"Companies with Red Flags: {red_flags}/{len(verifications)}")
        
        print(f"\n{'='*80}\n")
        
    finally:
        db.close()


def view_summary_table():
    """View summary table format"""
    SessionLocal, _ = get_session_factory()
    db = SessionLocal()
    
    try:
        verifications = db.query(LOBVerification).order_by(
            LOBVerification.created_at.desc()
        ).all()
        
        print("=" * 120)
        print("COMPANY DATA SUMMARY TABLE")
        print("=" * 120)
        print(f"\n{'ID':<5} {'Company':<25} {'Country':<8} {'URL Found':<12} {'Sources':<8} {'Activity':<12} {'Red Flag':<10}")
        print("-" * 120)
        
        for v in verifications:
            company = v.client[:24] if len(v.client) <= 24 else v.client[:21] + "..."
            url_found = "Yes" if v.website_source else "No"
            sources_count = len(v.sources) if v.sources else 0
            activity = v.activity_level or "N/A"
            red_flag = "Yes" if v.is_red_flag else "No"
            
            print(f"{v.id:<5} {company:<25} {v.client_country:<8} {url_found:<12} {sources_count:<8} {activity:<12} {red_flag:<10}")
        
        print("=" * 120)
        print(f"\nTotal Records: {len(verifications)}\n")
        
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--table":
        view_summary_table()
    else:
        view_all_companies()

