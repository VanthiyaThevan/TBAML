"""
EU Consolidated Sanctions List Parser
Parses the EU Full Sanctions List XML file and provides search functionality
Source: https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList/content
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from app.core.logging import get_logger

logger = get_logger(__name__)

# EU XML namespace
NS = {
    "ns": "http://eu.europa.ec/fpi/fsd/export"
}


class EUSanctionsParser:
    """Parser for EU Consolidated Sanctions List XML file"""
    
    def __init__(self, xml_file_path: Optional[str] = None):
        """
        Initialize EU sanctions parser
        
        Args:
            xml_file_path: Path to EU sanctions XML file
                          If None, uses default path in project data folder
        """
        if xml_file_path is None:
            # Default to project data folder
            project_root = Path(__file__).parent.parent.parent
            xml_file_path = project_root / "data" / "eu" / "eu_sanctions.xml"
        
        self.xml_file_path = Path(xml_file_path)
        self.sanction_entries: List[Dict[str, Any]] = []
        self.indexed_names: Dict[str, List[Dict[str, Any]]] = {}
        self.loaded = False
    
    def load_file(self) -> bool:
        """
        Load and parse the EU sanctions XML file
        
        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.xml_file_path.exists():
            logger.error(f"EU sanctions file not found: {self.xml_file_path}")
            return False
        
        try:
            logger.info(f"Loading EU sanctions file: {self.xml_file_path} (size: {self.xml_file_path.stat().st_size / (1024*1024):.1f} MB)")
            
            # Parse XML with iterparse for large files
            self.sanction_entries = []
            self.indexed_names = {}
            
            entry_count = 0
            
            for event, elem in ET.iterparse(str(self.xml_file_path), events=("start", "end")):
                if event == "start" and elem.tag.endswith("}sanctionEntity"):
                    # Process a sanctionEntity entry
                    entry = self._parse_sanction_entity(elem)
                    if entry:
                        self.sanction_entries.append(entry)
                        # Index by name for faster searching
                        names = entry.get("names", [])
                        for name in names:
                            name_lower = name.lower()
                            if name_lower not in self.indexed_names:
                                self.indexed_names[name_lower] = []
                            self.indexed_names[name_lower].append(entry)
                        
                        entry_count += 1
                        if entry_count % 500 == 0:
                            logger.debug(f"Loaded {entry_count} EU sanctions entries...")
                    
                    # Clear element to free memory
                    elem.clear()
            
            logger.info(f"Successfully loaded {len(self.sanction_entries)} EU sanctions entries")
            self.loaded = True
            return True
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error loading EU sanctions file: {str(e)}", exc_info=True)
            return False
    
    def _parse_sanction_entity(self, entity_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """
        Parse a sanctionEntity entry from XML
        
        Args:
            entity_elem: XML element for sanctionEntity
            
        Returns:
            Dictionary with sanction entity data or None
        """
        try:
            # Get logical ID
            logical_id = entity_elem.get("logicalId", "")
            united_nation_id = entity_elem.get("unitedNationId", "")
            
            # Get remark
            remark_elem = entity_elem.find("ns:remark", NS)
            remark = remark_elem.text if remark_elem is not None and remark_elem.text else ""
            
            # Get subject type (person or entity)
            subject_type_elem = entity_elem.find("ns:subjectType", NS)
            subject_type = subject_type_elem.get("code", "") if subject_type_elem is not None else ""
            
            # Extract names/aliases
            names = []
            for name_alias in entity_elem.findall("ns:nameAlias", NS):
                # Get whole name first
                whole_name = name_alias.get("wholeName", "").strip()
                if whole_name:
                    names.append(whole_name)
                else:
                    # Construct from first/middle/last
                    first = name_alias.get("firstName", "").strip()
                    middle = name_alias.get("middleName", "").strip()
                    last = name_alias.get("lastName", "").strip()
                    constructed = " ".join([x for x in [first, middle, last] if x])
                    if constructed:
                        names.append(constructed)
            
            # Extract regulations
            regulations = []
            for regulation in entity_elem.findall("ns:regulation", NS):
                reg_info = {
                    "regulationType": regulation.get("regulationType", ""),
                    "numberTitle": regulation.get("numberTitle", ""),
                    "publicationDate": regulation.get("publicationDate", ""),
                    "programme": regulation.get("programme", ""),
                    "publicationUrl": ""
                }
                pub_url_elem = regulation.find("ns:publicationUrl", NS)
                if pub_url_elem is not None and pub_url_elem.text:
                    reg_info["publicationUrl"] = pub_url_elem.text
                regulations.append(reg_info)
            
            # Extract citizenship
            citizenships = []
            for citizenship in entity_elem.findall("ns:citizenship", NS):
                citizenships.append({
                    "countryCode": citizenship.get("countryIso2Code", ""),
                    "country": citizenship.get("countryDescription", "")
                })
            
            # Extract birthdates
            birthdates = []
            for birthdate in entity_elem.findall("ns:birthdate", NS):
                birthdates.append({
                    "date": birthdate.get("birthdate", ""),
                    "year": birthdate.get("year", ""),
                    "month": birthdate.get("monthOfYear", ""),
                    "day": birthdate.get("dayOfMonth", ""),
                    "city": birthdate.get("city", ""),
                    "countryCode": birthdate.get("countryIso2Code", ""),
                    "country": birthdate.get("countryDescription", "")
                })
            
            # Extract address information
            addresses = []
            for address in entity_elem.findall("ns:address", NS):
                addresses.append({
                    "street": address.get("street", ""),
                    "city": address.get("city", ""),
                    "zipCode": address.get("zipCode", ""),
                    "countryCode": address.get("countryIso2Code", ""),
                    "country": address.get("countryDescription", "")
                })
            
            # Only return if we have at least one name
            if not names:
                return None
            
            entry = {
                "logical_id": logical_id,
                "united_nation_id": united_nation_id,
                "remark": remark,
                "subject_type": subject_type,  # "person" or "entity"
                "names": names,
                "regulations": regulations,
                "citizenships": citizenships,
                "birthdates": birthdates,
                "addresses": addresses
            }
            
            return entry
            
        except Exception as e:
            logger.warning(f"Error parsing sanction entity: {str(e)}")
            return None
    
    def search_entity(self, entity_name: str, exact_match: bool = False) -> List[Dict[str, Any]]:
        """
        Search for an entity in the EU sanctions list
        
        Args:
            entity_name: Name to search for
            exact_match: If True, only return exact matches (case-insensitive)
                        If False, return partial matches
            
        Returns:
            List of matching entries
        """
        if not self.loaded:
            logger.warning("EU sanctions file not loaded. Loading now...")
            if not self.load_file():
                return []
        
        matches = []
        entity_name_lower = entity_name.lower().strip()
        
        if exact_match:
            # Exact match (case-insensitive)
            if entity_name_lower in self.indexed_names:
                matches.extend(self.indexed_names[entity_name_lower])
        else:
            # Partial match - check all indexed names
            for indexed_name, entries in self.indexed_names.items():
                if entity_name_lower in indexed_name or indexed_name in entity_name_lower:
                    matches.extend(entries)
        
        # Remove duplicates based on logical_id
        seen_ids = set()
        unique_matches = []
        for match in matches:
            logical_id = match.get("logical_id", "")
            if logical_id and logical_id not in seen_ids:
                seen_ids.add(logical_id)
                unique_matches.append(match)
        
        return unique_matches
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the loaded sanctions list
        
        Returns:
            Dictionary with statistics
        """
        if not self.loaded:
            return {"loaded": False}
        
        total_names = sum(len(entry.get("names", [])) for entry in self.sanction_entries)
        
        return {
            "loaded": True,
            "total_entries": len(self.sanction_entries),
            "total_names": total_names,
            "indexed_names": len(self.indexed_names),
            "file_path": str(self.xml_file_path),
            "file_size_mb": self.xml_file_path.stat().st_size / (1024 * 1024) if self.xml_file_path.exists() else 0,
            "source": "EU Consolidated Sanctions List",
            "source_url": "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList/content"
        }


# Singleton instance for caching
_parser_instance: Optional[EUSanctionsParser] = None


def get_eu_sanctions_parser() -> EUSanctionsParser:
    """Get singleton EU sanctions parser instance"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = EUSanctionsParser()
        _parser_instance.load_file()
    return _parser_instance
