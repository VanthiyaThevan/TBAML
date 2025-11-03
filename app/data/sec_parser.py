"""
SEC EDGAR Company Tickers Parser
Parses the SEC company tickers JSON file and provides search functionality
"""

import json
import gzip
from typing import Dict, List, Optional, Any
from pathlib import Path
from app.core.logging import get_logger

logger = get_logger(__name__)


class SECCompanyParser:
    """Parser for SEC EDGAR company tickers file"""
    
    def __init__(self, json_file_path: Optional[str] = None):
        """
        Initialize SEC company parser
        
        Args:
            json_file_path: Path to SEC company tickers JSON file
                           If None, uses default path in project data folder
        """
        if json_file_path is None:
            # Default to project data folder
            project_root = Path(__file__).parent.parent.parent
            json_file_path = project_root / "data" / "sec" / "company_tickers.json"
        
        self.json_file_path = Path(json_file_path)
        self.companies: Dict[str, Dict[str, Any]] = {}
        self.indexed_names: Dict[str, List[Dict[str, Any]]] = {}
        self.indexed_tickers: Dict[str, Dict[str, Any]] = {}
        self.loaded = False
    
    def load_file(self) -> bool:
        """
        Load and parse the SEC company tickers JSON file
        
        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.json_file_path.exists():
            logger.error(f"SEC company tickers file not found: {self.json_file_path}")
            return False
        
        try:
            logger.info(f"Loading SEC company tickers file: {self.json_file_path} (size: {self.json_file_path.stat().st_size / 1024:.1f} KB)")
            
            # Try to open as gzip first, then regular JSON
            try:
                # Check if file is gzip compressed
                with open(self.json_file_path, 'rb') as f:
                    is_gzip = f.read(2) == b'\x1f\x8b'
                
                if is_gzip:
                    with gzip.open(self.json_file_path, 'rt', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    with open(self.json_file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
            except Exception as e:
                logger.warning(f"Error reading file, trying alternative method: {str(e)}")
                # Fallback: try regular JSON
                with open(self.json_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # Parse the data
            # SEC tickers file format: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
            self.companies = {}
            self.indexed_names = {}
            self.indexed_tickers = {}
            
            for key, company_info in data.items():
                if isinstance(company_info, dict):
                    cik = str(company_info.get("cik_str", ""))
                    ticker = company_info.get("ticker", "").upper()
                    title = company_info.get("title", "").strip()
                    
                    if cik and (ticker or title):
                        company = {
                            "cik": cik,
                            "ticker": ticker,
                            "name": title,
                            "cik_str": cik.zfill(10),  # Pad CIK to 10 digits
                        }
                        
                        # Store by CIK
                        self.companies[cik] = company
                        
                        # Index by ticker
                        if ticker:
                            self.indexed_tickers[ticker.upper()] = company
                        
                        # Index by name (case-insensitive)
                        if title:
                            title_lower = title.lower()
                            if title_lower not in self.indexed_names:
                                self.indexed_names[title_lower] = []
                            self.indexed_names[title_lower].append(company)
                            
                            # Also index by partial matches (for search)
                            words = title_lower.split()
                            for word in words:
                                if len(word) > 3:  # Only index words longer than 3 chars
                                    if word not in self.indexed_names:
                                        self.indexed_names[word] = []
                                    if company not in self.indexed_names[word]:
                                        self.indexed_names[word].append(company)
            
            logger.info(f"Successfully loaded {len(self.companies)} SEC companies")
            logger.info(f"Indexed {len(self.indexed_names)} name variations")
            logger.info(f"Indexed {len(self.indexed_tickers)} tickers")
            
            self.loaded = True
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error loading SEC company tickers file: {str(e)}", exc_info=True)
            return False
    
    def search_company(
        self,
        company_name: str,
        exact_match: bool = False,
        use_ticker: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for a company in the SEC EDGAR database
        
        Args:
            company_name: Company name or ticker to search for
            exact_match: If True, only return exact matches (case-insensitive)
                        If False, return partial matches
            use_ticker: If True, also search by ticker symbol
        
        Returns:
            List of matching company records
        """
        if not self.loaded:
            logger.warning("SEC company tickers file not loaded. Loading now...")
            if not self.load_file():
                return []
        
        matches = []
        search_term = company_name.upper().strip() if use_ticker else company_name.lower().strip()
        
        # Try ticker search first if enabled
        if use_ticker and search_term in self.indexed_tickers:
            matches.append(self.indexed_tickers[search_term])
        
        # Name search
        if exact_match:
            # Exact match (case-insensitive)
            search_term_lower = company_name.lower().strip()
            if search_term_lower in self.indexed_names:
                matches.extend(self.indexed_names[search_term_lower])
        else:
            # Partial match - check all indexed names
            search_term_lower = company_name.lower().strip()
            for indexed_name, companies in self.indexed_names.items():
                if search_term_lower in indexed_name or indexed_name in search_term_lower:
                    matches.extend(companies)
        
        # Remove duplicates based on CIK
        seen_ciks = set()
        unique_matches = []
        for match in matches:
            cik = match.get("cik", "")
            if cik and cik not in seen_ciks:
                seen_ciks.add(cik)
                unique_matches.append(match)
        
        return unique_matches
    
    def get_company_by_cik(self, cik: str) -> Optional[Dict[str, Any]]:
        """
        Get company by CIK number
        
        Args:
            cik: CIK number (can be with or without leading zeros)
        
        Returns:
            Company record or None
        """
        if not self.loaded:
            if not self.load_file():
                return None
        
        # Try with padding
        cik_padded = cik.zfill(10)
        if cik_padded in self.companies:
            return self.companies[cik_padded]
        
        # Try without padding
        cik_no_pad = cik.lstrip('0')
        if cik_no_pad in self.companies:
            return self.companies[cik_no_pad]
        
        return None
    
    def get_company_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get company by ticker symbol
        
        Args:
            ticker: Ticker symbol (e.g., "AAPL")
        
        Returns:
            Company record or None
        """
        if not self.loaded:
            if not self.load_file():
                return None
        
        return self.indexed_tickers.get(ticker.upper())
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the loaded company database
        
        Returns:
            Dictionary with statistics
        """
        if not self.loaded:
            return {"loaded": False}
        
        return {
            "loaded": True,
            "total_companies": len(self.companies),
            "indexed_names": len(self.indexed_names),
            "indexed_tickers": len(self.indexed_tickers),
            "file_path": str(self.json_file_path),
            "file_size_kb": self.json_file_path.stat().st_size / 1024 if self.json_file_path.exists() else 0
        }


# Singleton instance for caching
_parser_instance: Optional[SECCompanyParser] = None


def get_sec_parser() -> SECCompanyParser:
    """Get singleton SEC parser instance"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = SECCompanyParser()
        _parser_instance.load_file()
    return _parser_instance

