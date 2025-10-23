"""
Service for interacting with DeFi Llama API
"""

import requests
import logging
from typing import List, Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..constants.api import PROTOCOLS_ENDPOINT, REQUEST_TIMEOUT, MAX_RETRIES
from ..models.protocol import Protocol


class DeFiLlamaService:
    """
    Service class for DeFi Llama API interactions
    """

    def __init__(self):
        self.session = self._create_session()
        self.logger = logging.getLogger(__name__)

    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry strategy
        """
        session = requests.Session()

        # Retry strategy
        retry_strategy = Retry(
            total=MAX_RETRIES, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["HEAD", "GET", "OPTIONS"], backoff_factor=1
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def get_all_protocols(self) -> List[Dict[str, Any]]:
        """
        Fetch all protocols from DeFi Llama API

        Returns:
            List of protocol dictionaries
        """
        try:
            self.logger.info("Fetching protocols from DeFi Llama API...")

            response = self.session.get(PROTOCOLS_ENDPOINT, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            protocols_data = response.json()
            self.logger.info(f"Successfully fetched {len(protocols_data)} protocols")

            return protocols_data

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching protocols: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise

    def get_protocols_by_categories(self, categories: List[str]) -> List[Protocol]:
        """
        Get protocols filtered by categories

        Args:
            categories: List of category names to filter by

        Returns:
            List of Protocol objects
        """
        try:
            # Fetch all protocols
            all_protocols_data = self.get_all_protocols()

            # Convert to Protocol objects and filter by categories
            protocols = []
            for protocol_data in all_protocols_data:
                try:
                    protocol = Protocol.from_dict(protocol_data)
                    if protocol.category in categories:
                        protocols.append(protocol)
                except Exception as e:
                    self.logger.warning(f"Error parsing protocol {protocol_data.get('name', 'Unknown')}: {e}")
                    continue

            self.logger.info(f"Found {len(protocols)} protocols in categories: {categories}")
            return protocols

        except Exception as e:
            self.logger.error(f"Error getting protocols by categories: {e}")
            raise
