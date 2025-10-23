"""
Utility functions for data processing
"""

import csv
import json
import logging
import math
from typing import List, Dict, Any
from tabulate import tabulate
from ..models.protocol import Protocol


class DataProcessor:
    """
    Utility class for processing protocol data
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_top_protocols_by_tvl(self, protocols: List[Protocol], top_count: int = 20) -> List[Protocol]:
        """
        Get top protocols sorted by TVL (Total Value Locked)

        Args:
            protocols: List of Protocol objects
            top_count: Number of top protocols to return

        Returns:
            List of top protocols sorted by TVL (descending)
        """
        try:
            # Filter out protocols with None or negative TVL
            valid_protocols = [p for p in protocols if p.tvl is not None and p.tvl > 0]

            # Sort by TVL descending
            sorted_protocols = sorted(valid_protocols, key=lambda x: x.tvl, reverse=True)

            # Return top N protocols
            top_protocols = sorted_protocols[:top_count]

            self.logger.info(f"Retrieved top {len(top_protocols)} protocols by TVL")
            return top_protocols

        except Exception as e:
            self.logger.error(f"Error processing protocols by TVL: {e}")
            raise

    def get_top_protocols_per_category(self, protocols: List[Protocol], top_count: int = 20) -> Dict[str, List[Protocol]]:
        """
        Get top N protocols for each category separately

        Args:
            protocols: List of Protocol objects
            top_count: Number of top protocols to return per category

        Returns:
            Dictionary with category as key and list of top protocols as value
        """
        try:
            # Group protocols by category first
            grouped_protocols = self.group_protocols_by_category(protocols)

            # Get top N for each category
            top_per_category = {}

            for category, category_protocols in grouped_protocols.items():
                top_protocols = self.get_top_protocols_by_tvl(category_protocols, top_count)
                if top_protocols:  # Only include categories that have valid protocols
                    top_per_category[category] = top_protocols

            total_protocols = sum(len(protocols) for protocols in top_per_category.values())
            self.logger.info(f"Retrieved top {top_count} protocols for {len(top_per_category)} categories (total: {total_protocols} protocols)")

            return top_per_category

        except Exception as e:
            self.logger.error(f"Error processing top protocols per category: {e}")
            raise

    def group_protocols_by_category(self, protocols: List[Protocol]) -> Dict[str, List[Protocol]]:
        """
        Group protocols by category

        Args:
            protocols: List of Protocol objects

        Returns:
            Dictionary with category as key and list of protocols as value
        """
        try:
            grouped = {}

            for protocol in protocols:
                category = protocol.category
                if category not in grouped:
                    grouped[category] = []
                grouped[category].append(protocol)

            self.logger.info(f"Grouped protocols into {len(grouped)} categories")
            return grouped

        except Exception as e:
            self.logger.error(f"Error grouping protocols by category: {e}")
            raise

    def format_tvl(self, tvl: float) -> str:
        """
        Format TVL value for display

        Args:
            tvl: TVL value

        Returns:
            Formatted TVL string
        """
        if tvl >= 1_000_000_000:
            return f"${tvl / 1_000_000_000:.2f}B"
        elif tvl >= 1_000_000:
            return f"${tvl / 1_000_000:.2f}M"
        elif tvl >= 1_000:
            return f"${tvl / 1_000:.2f}K"
        else:
            return f"${tvl:.2f}"

    def print_protocols_summary(self, protocols: List[Protocol], title: str = "Protocols Summary"):
        """
        Print a formatted table summary of protocols

        Args:
            protocols: List of Protocol objects
            title: Title for the summary
        """
        try:
            print(f"\n{'='*80}")
            print(f"🏆 {title}")
            print(f"{'='*80}")

            # Prepare data for table
            table_data = []
            for i, protocol in enumerate(protocols, 1):
                tvl_formatted = self.format_tvl(protocol.tvl)

                # Truncate long names for better display
                name_display = protocol.name[:35] + "..." if len(protocol.name) > 35 else protocol.name

                # Add change indicators
                change_1d = protocol.change_1d if protocol.change_1d is not None else 0
                change_indicator = "📈" if change_1d > 0 else "📉" if change_1d < 0 else "➡️"
                change_display = f"{change_1d:+.2f}%" if change_1d != 0 else "0.00%"

                # Format chains for display
                chains_display = ""
                if protocol.chains:
                    if len(protocol.chains) <= 3:
                        chains_display = ", ".join(protocol.chains[:3])
                    else:
                        chains_display = f"{', '.join(protocol.chains[:2])}, +{len(protocol.chains)-2} more"
                else:
                    chains_display = "N/A"

                table_data.append([f"#{i}", name_display, protocol.category, tvl_formatted, f"{change_indicator} {change_display}", chains_display])

            # Create table with headers
            headers = ["Rank", "Protocol Name", "Category", "TVL", "24h Change", "Chains"]

            print(tabulate(table_data, headers=headers, tablefmt="grid", stralign="left", numalign="right"))

            # Summary statistics
            total_tvl = sum(p.tvl for p in protocols if p.tvl)
            avg_tvl = total_tvl / len(protocols) if protocols else 0

            print(f"\n📊 Summary Statistics:")
            summary_table = [
                ["Total Protocols", f"{len(protocols):,}"],
                ["Total TVL", self.format_tvl(total_tvl)],
                ["Average TVL", self.format_tvl(avg_tvl)],
                ["Highest TVL", self.format_tvl(protocols[0].tvl) if protocols else "$0"],
                ["Lowest TVL", self.format_tvl(protocols[-1].tvl) if protocols else "$0"],
            ]

            print(tabulate(summary_table, headers=["Metric", "Value"], tablefmt="simple", stralign="left"))
            print("=" * 80)

        except Exception as e:
            self.logger.error(f"Error printing protocols summary: {e}")
            raise

    def print_protocols_by_category_summary(self, protocols_by_category: Dict[str, List[Protocol]]):
        """
        Print a formatted summary of protocols grouped by category with beautiful tables

        Args:
            protocols_by_category: Dictionary with category as key and list of protocols as value
        """
        try:
            total_protocols = sum(len(protocols) for protocols in protocols_by_category.values())
            total_tvl = sum(sum(p.tvl for p in protocols if p.tvl) for protocols in protocols_by_category.values())

            # Overall summary table
            print(f"\n{'='*100}")
            print(f"📊 DEFI LLAMA PROTOCOL ANALYSIS - COMPREHENSIVE REPORT")
            print(f"{'='*100}")

            # Category overview table
            overview_data = []
            for category, protocols in protocols_by_category.items():
                category_tvl = sum(p.tvl for p in protocols if p.tvl)
                avg_tvl = category_tvl / len(protocols) if protocols else 0
                percentage = (category_tvl / total_tvl * 100) if total_tvl > 0 else 0

                overview_data.append(
                    [f"🏷️ {category}", f"{len(protocols):,}", self.format_tvl(category_tvl), self.format_tvl(avg_tvl), f"{percentage:.1f}%"]
                )

            # Sort by TVL descending
            overview_data.sort(
                key=lambda x: float(x[2].replace("$", "").replace("B", "000000000").replace("M", "000000").replace("K", "000").replace(",", "")),
                reverse=True,
            )

            print(f"\n📈 CATEGORY OVERVIEW:")
            print(
                tabulate(
                    overview_data,
                    headers=["Category", "Protocols", "Total TVL", "Avg TVL", "% of Total"],
                    tablefmt="fancy_grid",
                    stralign="left",
                    numalign="right",
                )
            )

            # Overall statistics
            print(f"\n🎯 OVERALL STATISTICS:")
            overall_stats = [
                ["Total Categories Analyzed", f"{len(protocols_by_category):,}"],
                ["Total Protocols Found", f"{total_protocols:,}"],
                ["Combined TVL", self.format_tvl(total_tvl)],
                ["Average TVL per Protocol", self.format_tvl(total_tvl / total_protocols if total_protocols > 0 else 0)],
                [
                    "Largest Category",
                    (
                        max(protocols_by_category.keys(), key=lambda k: sum(p.tvl for p in protocols_by_category[k] if p.tvl))
                        if protocols_by_category
                        else "N/A"
                    ),
                ],
            ]

            print(tabulate(overall_stats, headers=["Metric", "Value"], tablefmt="simple_grid", stralign="left"))

            print(f"\n{'='*100}")

            # Detailed tables for each category
            for category, protocols in protocols_by_category.items():
                category_tvl = sum(p.tvl for p in protocols if p.tvl)
                self.print_protocols_summary(protocols, f"Top {len(protocols)} {category} Protocols (Total TVL: {self.format_tvl(category_tvl)})")

        except Exception as e:
            self.logger.error(f"Error printing category summary: {e}")
            raise

    def export_to_csv(self, protocols: List[Protocol], filename: str = "protocols_data.csv", sort_by_tvl: bool = True) -> str:
        """
        Export protocols data to CSV file with specified fields

        Args:
            protocols: List of Protocol objects
            filename: Output CSV filename
            sort_by_tvl: Whether to sort protocols by TVL before export (for ranking)

        Returns:
            Path to the created CSV file
        """
        try:
            # Group protocols by category first
            grouped_protocols = self.group_protocols_by_category(protocols)

            # Prepare CSV data with separate ranking for each category
            csv_data = []

            for category, category_protocols in grouped_protocols.items():
                # Sort protocols within each category by TVL if requested
                if sort_by_tvl:
                    valid_protocols = [p for p in category_protocols if p.tvl is not None and p.tvl > 0]
                    sorted_protocols = sorted(valid_protocols, key=lambda x: x.tvl, reverse=True)
                else:
                    sorted_protocols = category_protocols

                # Add protocols with category-specific ranking
                for rank, protocol in enumerate(sorted_protocols, 1):
                    # Format chains as comma-separated string for CSV
                    chains_str = ", ".join(protocol.chains) if protocol.chains else ""

                    csv_data.append(
                        {
                            "category": protocol.category or "",
                            "rank": rank,  # Rank within category
                            "protocol_name": protocol.name or "",
                            "tvl": math.floor(protocol.tvl) if protocol.tvl is not None else 0,
                            "chains": chains_str,  # Formatted as string
                            "description": protocol.description or "",
                        }
                    )

            # Sort final data by category name for organized output
            csv_data.sort(key=lambda x: (x["category"], x["rank"]))

            # Write to CSV file
            fieldnames = ["category", "rank", "protocol_name", "tvl", "chains", "description"]

            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)

            self.logger.info(f"Successfully exported {len(csv_data)} protocols to {filename}")
            print(f"✅ Data exported successfully to: {filename}")
            print(f"📊 Total protocols exported: {len(csv_data):,}")
            print(f"📂 Categories: {len(grouped_protocols):,}")

            # Print summary by category
            for category, category_protocols in grouped_protocols.items():
                valid_count = len([p for p in category_protocols if p.tvl is not None and p.tvl > 0])
                print(f"   └─ {category}: {valid_count} protocols")

            return filename

        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}")
            raise
