"""
Protocol Analysis Job
"""

import logging
from typing import List, Dict, Any
from .data_processor import DataProcessor
from ..services.defillama_service import DeFiLlamaService
from ..constants.api import DEFAULT_TOP_COUNT


class ProtocolAnalysisJob:
    """
    Job for analyzing DeFi protocols
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.defillama_service = DeFiLlamaService()
        self.data_processor = DataProcessor()

    def analyze_custom_categories(self, categories: List[str], top_count: int = DEFAULT_TOP_COUNT) -> Dict[str, List[Any]]:
        """
        Analyze protocols for custom categories

        Args:
            categories: List of category names to analyze
            top_count: Number of top protocols to return per category

        Returns:
            Dictionary with category as key and list of top protocols as value
        """
        try:
            self.logger.info(f"Starting analysis for categories: {', '.join(categories)}")
            self.logger.info(f"Getting top {top_count} protocols for each category")

            # Fetch protocols by categories
            protocols = self.defillama_service.get_protocols_by_categories(categories)

            if not protocols:
                self.logger.warning("No protocols found for the specified categories")
                return {}

            # Get top protocols per category
            top_protocols_per_category = self.data_processor.get_top_protocols_per_category(protocols, top_count)

            # Display results
            self.data_processor.print_protocols_by_category_summary(top_protocols_per_category)

            # Export to CSV
            all_protocols = []
            for category_protocols in top_protocols_per_category.values():
                all_protocols.extend(category_protocols)

            if all_protocols:
                csv_filename = f"defi_protocols_analysis_{'-'.join(categories)}.csv"
                self.data_processor.export_to_csv(all_protocols, csv_filename)

            return top_protocols_per_category

        except Exception as e:
            self.logger.error(f"Error in protocol analysis: {e}")
            raise

    def analyze_all_protocols(self, top_count: int = DEFAULT_TOP_COUNT) -> Dict[str, List[Any]]:
        """
        Analyze all protocols

        Args:
            top_count: Number of top protocols to return per category

        Returns:
            Dictionary with category as key and list of top protocols as value
        """
        try:
            self.logger.info("Starting analysis for all protocols")
            
            # Fetch all protocols
            protocols = self.defillama_service.get_all_protocols()

            if not protocols:
                self.logger.warning("No protocols found")
                return {}

            # Get top protocols per category
            top_protocols_per_category = self.data_processor.get_top_protocols_per_category(protocols, top_count)

            # Display results
            self.data_processor.print_protocols_by_category_summary(top_protocols_per_category)

            # Export to CSV
            all_protocols = []
            for category_protocols in top_protocols_per_category.values():
                all_protocols.extend(category_protocols)

            if all_protocols:
                csv_filename = "defi_protocols_analysis_all.csv"
                self.data_processor.export_to_csv(all_protocols, csv_filename)

            return top_protocols_per_category

        except Exception as e:
            self.logger.error(f"Error in all protocols analysis: {e}")
            raise
