"""
Publication Date Extractor
Extracts publication dates from scraped website content
"""

import re
from typing import Optional, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from app.core.logging import get_logger

logger = get_logger(__name__)


class PublicationDateExtractor:
    """Extracts publication dates from websites"""
    
    def __init__(self):
        """Initialize date extractor"""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (TBAML-System/1.0) Compatible Bot"
        })
    
    def extract_from_url(self, url: str) -> Optional[str]:
        """
        Extract publication date from a website URL
        
        Args:
            url: Website URL
        
        Returns:
            Publication date string or None
        """
        if not url:
            return None
        
        try:
            logger.info(f"Extracting publication date from: {url}")
            response = self.session.get(url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Method 1: Check meta tags
            date = self._extract_from_meta_tags(soup)
            if date:
                return date
            
            # Method 2: Check structured data (JSON-LD, schema.org)
            date = self._extract_from_structured_data(soup)
            if date:
                return date
            
            # Method 3: Look for date patterns in content
            date = self._extract_from_content(soup)
            if date:
                return date
            
            # Method 4: Check article dates, copyright, etc.
            date = self._extract_from_common_patterns(soup)
            if date:
                return date
            
            logger.debug(f"Could not extract date from {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting date from {url}", error=str(e))
            return None
    
    def _extract_from_meta_tags(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date from meta tags"""
        # Check article:published_time
        meta = soup.find('meta', property='article:published_time')
        if meta and meta.get('content'):
            return self._normalize_date(meta['content'])
        
        # Check og:published_time
        meta = soup.find('meta', property='og:published_time')
        if meta and meta.get('content'):
            return self._normalize_date(meta['content'])
        
        # Check datePublished
        meta = soup.find('meta', attrs={'name': 'datePublished'})
        if meta and meta.get('content'):
            return self._normalize_date(meta['content'])
        
        # Check DC.date
        meta = soup.find('meta', attrs={'name': 'DC.date'})
        if meta and meta.get('content'):
            return self._normalize_date(meta['content'])
        
        return None
    
    def _extract_from_structured_data(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date from structured data (JSON-LD, schema.org)"""
        # Look for JSON-LD scripts
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                import json
                data = json.loads(script.string)
                
                # Check for datePublished
                if isinstance(data, dict):
                    date = data.get('datePublished') or data.get('datePublishedOriginal')
                    if date:
                        return self._normalize_date(date)
                    
                    # Check nested structures
                    if '@graph' in data:
                        for item in data['@graph']:
                            if 'datePublished' in item:
                                return self._normalize_date(item['datePublished'])
            except Exception:
                continue
        
        return None
    
    def _extract_from_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date from page content using patterns"""
        text = soup.get_text()
        
        # Common date patterns
        patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',  # MM/DD/YYYY or DD/MM/YYYY
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',  # YYYY/MM/DD
            r'(Published.*?(\d{1,2}\s+\w+\s+\d{4}))',  # Published: DD Month YYYY
            r'(Updated.*?(\d{1,2}\s+\w+\s+\d{4}))',   # Updated: DD Month YYYY
            r'(\w+\s+\d{1,2},?\s+\d{4})',             # Month DD, YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1) if len(match.groups()) > 0 else match.group(0)
                try:
                    normalized = self._normalize_date(date_str)
                    if normalized:
                        return normalized
                except Exception:
                    continue
        
        return None
    
    def _extract_from_common_patterns(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date from common HTML patterns"""
        # Check time tags
        time_tag = soup.find('time')
        if time_tag:
            datetime_attr = time_tag.get('datetime')
            if datetime_attr:
                return self._normalize_date(datetime_attr)
            if time_tag.string:
                return self._normalize_date(time_tag.string)
        
        # Check copyright year (fallback)
        copyright = soup.find(string=re.compile(r'Copyright.*?(\d{4})', re.IGNORECASE))
        if copyright:
            match = re.search(r'(\d{4})', copyright)
            if match:
                year = match.group(1)
                # Use current year as fallback (not ideal but better than nothing)
                return f"{year}-01-01"
        
        return None
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """
        Normalize date string to ISO format or readable format
        
        Args:
            date_str: Date string in various formats
        
        Returns:
            Normalized date string or None
        """
        if not date_str:
            return None
        
        # Clean up the string
        date_str = date_str.strip()
        
        # If already in ISO format
        if re.match(r'^\d{4}-\d{2}-\d{2}', date_str):
            return date_str.split('T')[0]  # Remove time if present
        
        # Try parsing common formats
        formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.split('T')[0].split()[0], fmt if '%H' not in fmt else fmt.split('T')[0].split()[0])
                return dt.strftime('%Y-%m-%d')
            except (ValueError, IndexError):
                continue
        
        # If can't parse, return as-is (might be useful)
        return date_str
    
    def update_publication_dates(self, verification_ids: Optional[list] = None) -> Dict[str, Any]:
        """
        Update publication dates for verifications
        
        Args:
            verification_ids: Optional list of verification IDs to update (all if None)
        
        Returns:
            Dictionary with update statistics
        """
        from app.models.base import get_session_factory
        from app.models.lob import LOBVerification
        
        SessionLocal, _ = get_session_factory()
        db = SessionLocal()
        
        stats = {
            "total": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0
        }
        
        try:
            query = db.query(LOBVerification)
            
            if verification_ids:
                query = query.filter(LOBVerification.id.in_(verification_ids))
            
            verifications = query.filter(
                LOBVerification.website_source.isnot(None),
                LOBVerification.publication_date.is_(None)
            ).all()
            
            stats["total"] = len(verifications)
            
            logger.info(f"Updating publication dates for {stats['total']} verifications")
            
            for v in verifications:
                try:
                    date = self.extract_from_url(v.website_source)
                    if date:
                        v.publication_date = date
                        stats["updated"] += 1
                        logger.info(f"Updated date for {v.client}: {date}")
                    else:
                        stats["skipped"] += 1
                except Exception as e:
                    stats["errors"] += 1
                    logger.error(f"Error updating date for {v.client}", error=str(e))
            
            db.commit()
            logger.info(f"Publication date update complete: {stats['updated']}/{stats['total']} updated")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating publication dates", error=str(e))
        finally:
            db.close()
        
        return stats

