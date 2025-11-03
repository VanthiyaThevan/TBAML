"""
Export LOB Verifications Table to CSV
Exports all data from lob_verifications table to CSV format
"""

import csv
import json
from datetime import datetime
from app.models.base import get_session_factory
from app.models.lob import LOBVerification


def export_to_csv(filename="lob_verifications.csv"):
    """Export lob_verifications table to CSV"""
    SessionLocal, _ = get_session_factory()
    db = SessionLocal()
    
    try:
        verifications = db.query(LOBVerification).order_by(
            LOBVerification.id.asc()
        ).all()
        
        print(f"Exporting {len(verifications)} records to CSV...")
        
        # Define CSV columns
        fieldnames = [
            "id",
            "client",
            "client_country",
            "client_role",
            "product_name",
            "ai_response",
            "website_source",
            "publication_date",
            "activity_level",
            "flags",
            "sources",
            "is_red_flag",
            "confidence_score",
            "data_collected_at",
            "data_freshness_score",
            "last_verified_at",
            "created_at",
            "updated_at"
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for v in verifications:
                # Format flags as JSON string
                flags_str = ""
                if v.flags:
                    if isinstance(v.flags, list):
                        flags_str = json.dumps(v.flags, ensure_ascii=False)
                    else:
                        flags_str = str(v.flags)
                
                # Format sources as JSON string
                sources_str = ""
                if v.sources:
                    if isinstance(v.sources, list):
                        sources_str = json.dumps(v.sources, ensure_ascii=False)
                    else:
                        sources_str = str(v.sources)
                
                # Format timestamps
                def format_ts(ts):
                    if ts:
                        if isinstance(ts, str):
                            return ts
                        return ts.strftime("%Y-%m-%d %H:%M:%S")
                    return ""
                
                row = {
                    "id": v.id,
                    "client": v.client or "",
                    "client_country": v.client_country or "",
                    "client_role": v.client_role or "",
                    "product_name": v.product_name or "",
                    "ai_response": v.ai_response or "",
                    "website_source": v.website_source or "",
                    "publication_date": v.publication_date or "",
                    "activity_level": v.activity_level or "",
                    "flags": flags_str,
                    "sources": sources_str,
                    "is_red_flag": str(v.is_red_flag) if v.is_red_flag is not None else "",
                    "confidence_score": v.confidence_score or "",
                    "data_collected_at": format_ts(v.data_collected_at),
                    "data_freshness_score": v.data_freshness_score or "",
                    "last_verified_at": format_ts(v.last_verified_at),
                    "created_at": format_ts(v.created_at),
                    "updated_at": format_ts(v.updated_at)
                }
                
                writer.writerow(row)
        
        print(f"✅ Successfully exported {len(verifications)} records to: {filename}")
        print(f"   File size: {get_file_size(filename)}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("EXPORT SUMMARY")
        print("=" * 80)
        print(f"Total Records: {len(verifications)}")
        print(f"With AI Response: {sum(1 for v in verifications if v.ai_response)}")
        print(f"With Activity Level: {sum(1 for v in verifications if v.activity_level and v.activity_level != 'Unknown')}")
        print(f"With Flags: {sum(1 for v in verifications if v.flags and (isinstance(v.flags, list) and len(v.flags) > 0))}")
        print(f"Red Flags: {sum(1 for v in verifications if v.is_red_flag)}")
        print("=" * 80)
        
    finally:
        db.close()


def get_file_size(filename):
    """Get file size in human-readable format"""
    import os
    size = os.path.getsize(filename)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


if __name__ == "__main__":
    import sys
    
    filename = sys.argv[1] if len(sys.argv) > 1 else "lob_verifications.csv"
    export_to_csv(filename)


