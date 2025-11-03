"""
Update UC1 Outputs with AI Analysis
Script to analyze companies and populate UC1 output fields in database
"""

from app.services.ai_service import AIService
from app.core.logging import get_logger

logger = get_logger(__name__)


def update_uc1_outputs(limit: int = 5, force_update: bool = False):
    """
    Update UC1 outputs for companies in database
    
    Args:
        limit: Number of companies to analyze (None for all)
        force_update: Whether to force update even if already analyzed
    """
    print("=" * 80)
    print("UPDATING UC1 OUTPUTS WITH AI ANALYSIS")
    print("=" * 80)
    print()
    
    ai_service = AIService()
    
    # Check current status
    print("Current Analysis Status:")
    status = ai_service.get_analysis_status()
    print(f"  Total Records: {status['total_records']}")
    print(f"  With AI Response: {status['with_ai_response']}/{status['total_records']} ({status['completion_percentage']:.1f}%)")
    print(f"  With Activity Level: {status['with_activity_level']}/{status['total_records']}")
    print(f"  With Flags: {status['with_flags']}/{status['total_records']}")
    print(f"  Red Flags: {status['red_flags']}/{status['total_records']}")
    print()
    
    # Run batch analysis
    print(f"Analyzing companies (limit: {limit if limit else 'all'}, force_update: {force_update})...")
    print()
    
    results = ai_service.analyze_batch(limit=limit, force_update=force_update)
    
    print("=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)
    print()
    print(f"Total Processed: {results['total']}")
    print(f"Successfully Analyzed: {results['analyzed']}")
    print(f"Skipped (already analyzed): {results['skipped']}")
    print(f"Errors: {results['errors']}")
    print()
    
    if results['details']:
        print("Details:")
        for detail in results['details'][:10]:  # Show first 10
            company = detail.get('company', 'Unknown')
            status = detail.get('status', 'unknown')
            
            if status == "analyzed":
                activity = detail.get('activity_level', 'Unknown')
                risk = detail.get('risk_level', 'Unknown')
                flags = detail.get('flags_count', 0)
                red_flag = "⚠️  RED FLAG" if detail.get('is_red_flag') else "✅"
                print(f"  {red_flag} {company}: {activity} ({risk}), {flags} flags")
            elif status == "already_analyzed":
                print(f"  ⏭️  {company}: Already analyzed")
            elif status == "error":
                error = detail.get('error', 'Unknown error')
                print(f"  ❌ {company}: Error - {error[:50]}")
        
        if len(results['details']) > 10:
            print(f"  ... and {len(results['details']) - 10} more")
    
    print()
    
    # Check updated status
    print("Updated Analysis Status:")
    updated_status = ai_service.get_analysis_status()
    print(f"  Total Records: {updated_status['total_records']}")
    print(f"  With AI Response: {updated_status['with_ai_response']}/{updated_status['total_records']} ({updated_status['completion_percentage']:.1f}%)")
    print(f"  With Activity Level: {updated_status['with_activity_level']}/{updated_status['total_records']}")
    print(f"  With Flags: {updated_status['with_flags']}/{updated_status['total_records']}")
    print(f"  Red Flags: {updated_status['red_flags']}/{updated_status['total_records']}")
    print()
    
    print("=" * 80)
    
    if results['analyzed'] > 0:
        print("✅ UC1 outputs updated successfully!")
    else:
        print("⚠️  No new analyses performed (may already be analyzed or errors occurred)")
    
    print("=" * 80)
    print()


if __name__ == "__main__":
    import sys
    
    limit = None
    force_update = False
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            limit = None
        elif sys.argv[1].isdigit():
            limit = int(sys.argv[1])
        elif sys.argv[1] == "--force":
            force_update = True
    
    if len(sys.argv) > 2:
        if sys.argv[2] == "--force":
            force_update = True
        elif sys.argv[2].isdigit():
            limit = int(sys.argv[2])
    
    update_uc1_outputs(limit=limit, force_update=force_update)

