"""
Data source connector architecture
Manages multiple data sources and orchestrates data collection
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from app.data.base import DataSource, DataCollectionResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataConnector:
    """Manages multiple data sources and coordinates data collection"""
    
    def __init__(self):
        """Initialize the data connector"""
        self.sources: Dict[str, DataSource] = {}
        self.collection_history: List[DataCollectionResult] = []
    
    def register_source(self, source: DataSource):
        """
        Register a data source
        
        Args:
            source: Data source instance to register
        """
        self.sources[source.name] = source
        logger.info(f"Registered data source: {source.name}")
    
    def collect_from_all_sources(
        self,
        query: Dict[str, Any],
        sources: Optional[List[str]] = None
    ) -> List[DataCollectionResult]:
        """
        Collect data from all registered sources (or specified sources)
        
        Args:
            query: Query parameters (client, country, product, etc.)
            sources: Optional list of source names to use (if None, use all)
        
        Returns:
            List of DataCollectionResult objects
        """
        results = []
        
        # Determine which sources to use
        sources_to_use = sources or list(self.sources.keys())
        
        logger.info(f"Collecting data from {len(sources_to_use)} sources", 
                   sources=sources_to_use, query=query)
        
        for source_name in sources_to_use:
            if source_name not in self.sources:
                logger.warning(f"Source not found: {source_name}")
                results.append(DataCollectionResult(
                    source=source_name,
                    success=False,
                    error=f"Source '{source_name}' not registered"
                ))
                continue
            
            source = self.sources[source_name]
            
            try:
                # Collect data from source
                data = source.fetch_data(query)
                
                # Validate data
                if source.validate_data(data):
                    result = DataCollectionResult(
                        source=source_name,
                        success=True,
                        data=data,
                        timestamp=datetime.utcnow()
                    )
                else:
                    result = DataCollectionResult(
                        source=source_name,
                        success=False,
                        error="Data validation failed"
                    )
                
                results.append(result)
                logger.info(f"Collected data from {source_name}", 
                           success=result.success)
                
            except Exception as e:
                logger.error(f"Error collecting from {source_name}", 
                           error=str(e), exc_info=True)
                results.append(DataCollectionResult(
                    source=source_name,
                    success=False,
                    error=str(e)
                ))
        
        # Store in history
        self.collection_history.extend(results)
        
        return results
    
    def aggregate_results(
        self,
        results: List[DataCollectionResult]
    ) -> Dict[str, Any]:
        """
        Aggregate data from multiple sources
        
        Args:
            results: List of DataCollectionResult objects
        
        Returns:
            Aggregated data dictionary
        """
        aggregated = {
            "sources": [],
            "data": {},
            "timestamp": datetime.utcnow().isoformat(),
            "success_count": 0,
            "total_count": len(results)
        }
        
        for result in results:
            source_info = {
                "name": result.source,
                "success": result.success,
                "timestamp": result.timestamp.isoformat()
            }
            
            if result.success and result.data:
                # Merge successful results
                aggregated["data"].update(result.data)
                aggregated["success_count"] += 1
            else:
                source_info["error"] = result.error
            
            aggregated["sources"].append(source_info)
        
        return aggregated
    
    def get_source_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all registered sources
        
        Returns:
            List of source information dictionaries
        """
        return [source.get_source_info() for source in self.sources.values()]

