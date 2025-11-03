"""
OFAC SDN List Parser
Parses the OFAC SDN Advanced XML file and provides search functionality
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from pathlib import Path
from app.core.logging import get_logger

logger = get_logger(__name__)

# OFAC XML namespace
NS = {
    "ns": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ADVANCED_XML"
}


class OFACSDNParser:
    """Parser for OFAC SDN Advanced XML files"""
    
    def __init__(self, xml_file_path: Optional[str] = None):
        """
        Initialize OFAC SDN parser
        
        Args:
            xml_file_path: Path to OFAC SDN Advanced XML file
                          If None, uses default path in project data folder
        """
        if xml_file_path is None:
            # Default to project data folder
            project_root = Path(__file__).parent.parent.parent
            xml_file_path = project_root / "data" / "ofac" / "sdn_advanced.xml"
        
        self.xml_file_path = Path(xml_file_path)
        self.tree: Optional[ET.ElementTree] = None
        self.root: Optional[ET.Element] = None
        self.sdn_entries: List[Dict[str, Any]] = []
        self.indexed_names: Dict[str, List[Dict[str, Any]]] = {}
        self.loaded = False
    
    def load_file(self) -> bool:
        """
        Load and parse the OFAC SDN XML file
        
        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.xml_file_path.exists():
            logger.error(f"OFAC SDN file not found: {self.xml_file_path}")
            return False
        
        try:
            logger.info(f"Loading OFAC SDN file: {self.xml_file_path} (size: {self.xml_file_path.stat().st_size / (1024*1024):.1f} MB)")
            
            # Parse XML with iterparse for large files
            self.sdn_entries = []
            self.indexed_names = {}
            
            # Count entries first to show progress
            entry_count = 0
            
            for event, elem in ET.iterparse(str(self.xml_file_path), events=("start", "end")):
                if event == "start" and elem.tag.endswith("}DistinctParty"):
                    # Process a DistinctParty entry
                    entry = self._parse_party_entry(elem)
                    if entry:
                        self.sdn_entries.append(entry)
                        # Index by name for faster searching
                        names = entry.get("names", [])
                        for name in names:
                            name_lower = name.lower()
                            if name_lower not in self.indexed_names:
                                self.indexed_names[name_lower] = []
                            self.indexed_names[name_lower].append(entry)
                        
                        entry_count += 1
                        if entry_count % 1000 == 0:
                            logger.debug(f"Loaded {entry_count} OFAC entries...")
                    
                    # Clear element to free memory
                    elem.clear()
            
            logger.info(f"Successfully loaded {len(self.sdn_entries)} OFAC SDN entries")
            self.loaded = True
            return True
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error loading OFAC SDN file: {str(e)}", exc_info=True)
            return False
    
    def _parse_party_entry(self, party_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """
        Parse a DistinctParty entry from XML
        
        Args:
            party_elem: XML element for DistinctParty
            
        Returns:
            Dictionary with party data or None
        """
        try:
            # Get profile ID from Profile element
            profile_elem = party_elem.find(".//ns:Profile", NS)
            profile_id = profile_elem.get("ID", "") if profile_elem is not None else ""
            
            # Extract names/aliases - names are in NamePartValue elements
            names = []
            
            # Find all DocumentedName elements
            for documented_name in party_elem.findall(".//ns:DocumentedName", NS):
                # Find all NamePartValue elements within this DocumentedName
                name_parts = []
                for name_part_value in documented_name.findall(".//ns:NamePartValue", NS):
                    name_text = name_part_value.text
                    if name_text:
                        name_parts.append(name_text.strip())
                
                # Join name parts
                if name_parts:
                    full_name = " ".join(name_parts)
                    if full_name and full_name not in names:
                        names.append(full_name)
            
            # If still no names, try alternative path
            if not names:
                for name_part_value in party_elem.findall(".//ns:NamePartValue", NS):
                    name_text = name_part_value.text
                    if name_text and name_text.strip():
                        name = name_text.strip()
                        if name not in names:
                            names.append(name)
            
            # Extract additional info
            dates_of_birth = []
            for dob in party_elem.findall(".//ns:DateOfBirth", NS):
                year = dob.find("ns:Year", NS)
                month = dob.find("ns:Month", NS)
                day = dob.find("ns:Day", NS)
                if year is not None and month is not None and day is not None:
                    dates_of_birth.append(f"{year.text}-{month.text}-{day.text}")
            
            # Extract places of birth
            places_of_birth = []
            for pob in party_elem.findall(".//ns:PlaceOfBirthList/ns:PlaceOfBirth", NS):
                city = pob.find("ns:City", NS)
                state = pob.find("ns:StateOrProvince", NS)
                country = pob.find("ns:Country", NS)
                
                location_parts = []
                if city is not None and city.text:
                    location_parts.append(city.text)
                if state is not None and state.text:
                    location_parts.append(state.text)
                if country is not None and country.text:
                    location_parts.append(country.text)
                
                if location_parts:
                    places_of_birth.append(", ".join(location_parts))
            
            # Extract program list
            programs = []
            for program in party_elem.findall(".//ns:ProgramList/ns:Program", NS):
                if program.text:
                    programs.append(program.text)
            
            # Extract remarks
            remarks = []
            for remark in party_elem.findall(".//ns:Remarks", NS):
                if remark.text:
                    remarks.append(remark.text.strip())
            
            entry = {
                "profile_id": profile_id,
                "names": names,
                "dates_of_birth": dates_of_birth,
                "places_of_birth": places_of_birth,
                "programs": programs,
                "remarks": remarks,
                "raw_xml": ET.tostring(party_elem, encoding="unicode")[:500]  # Store first 500 chars for reference
            }
            
            return entry if names else None  # Only return if we have at least one name
            
        except Exception as e:
            logger.warning(f"Error parsing party entry: {str(e)}")
            return None
    
    def search_entity(self, entity_name: str, exact_match: bool = False) -> List[Dict[str, Any]]:
        """
        Search for an entity in the OFAC SDN list
        
        Args:
            entity_name: Name to search for
            exact_match: If True, only return exact matches (case-insensitive)
                         If False, return partial matches
            
        Returns:
            List of matching entries
        """
        if not self.loaded:
            logger.warning("OFAC SDN file not loaded. Loading now...")
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
        
        # Remove duplicates based on profile_id
        seen_ids = set()
        unique_matches = []
        for match in matches:
            profile_id = match.get("profile_id", "")
            if profile_id and profile_id not in seen_ids:
                seen_ids.add(profile_id)
                unique_matches.append(match)
        
        return unique_matches
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the loaded SDN list
        
        Returns:
            Dictionary with statistics
        """
        if not self.loaded:
            return {"loaded": False}
        
        total_names = sum(len(entry.get("names", [])) for entry in self.sdn_entries)
        
        return {
            "loaded": True,
            "total_entries": len(self.sdn_entries),
            "total_names": total_names,
            "indexed_names": len(self.indexed_names),
            "file_path": str(self.xml_file_path),
            "file_size_mb": self.xml_file_path.stat().st_size / (1024 * 1024) if self.xml_file_path.exists() else 0
        }


# Singleton instance for caching
_parser_instance: Optional[OFACSDNParser] = None


def get_ofac_parser() -> OFACSDNParser:
    """Get singleton OFAC parser instance"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = OFACSDNParser()
        _parser_instance.load_file()
    return _parser_instance

