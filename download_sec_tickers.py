"""
Download SEC company tickers file with proper headers
"""

import requests
import json
import gzip
from pathlib import Path

def download_sec_tickers():
    """Download SEC company tickers JSON file"""
    
    url = "https://www.sec.gov/files/company_tickers.json"
    
    headers = {
        "User-Agent": "TBAML-System Company Registry Verification (contact: prabhugovindan@example.com)",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate",
        "Host": "www.sec.gov",
        "Connection": "keep-alive"
    }
    
    output_path = Path("data/sec/company_tickers.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading SEC company tickers from: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        # Check if response is JSON or HTML (blocked)
        content = response.content
        if content.startswith(b'<!DOCTYPE') or content.startswith(b'<html'):
            print("❌ SEC is blocking the request (returned HTML instead of JSON)")
            print("Response preview:")
            print(content[:500].decode('utf-8', errors='ignore'))
            return False
        
        # Try to parse as JSON
        try:
            # Check if it's gzip compressed
            if content.startswith(b'\x1f\x8b'):
                data = json.loads(gzip.decompress(content).decode('utf-8'))
                print("✅ File is gzip compressed, decompressed successfully")
            else:
                data = response.json()
                print("✅ File is plain JSON, parsed successfully")
            
            # Save the file
            with open(output_path, 'wb') as f:
                f.write(content)
            
            print(f"\n✅ Downloaded successfully!")
            print(f"   File: {output_path}")
            print(f"   Size: {len(content) / 1024:.2f} KB")
            print(f"   Companies: {len(data) if isinstance(data, dict) else 'N/A'}")
            
            # Show sample
            if isinstance(data, dict):
                print("\nSample entries:")
                for i, (key, value) in enumerate(list(data.items())[:5]):
                    print(f"  {key}: {value}")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {str(e)}")
            print(f"Content preview: {content[:500]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {str(e)}")
        return False

if __name__ == "__main__":
    download_sec_tickers()

