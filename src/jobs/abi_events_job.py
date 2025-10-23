"""
ABI Events Job
"""

import logging
import argparse
import json
import re
import tempfile
import os
from typing import Dict, Any
from ..services.abi_service import ABIEventService


class ABIEventsJob:
    """
    Job for extracting ABI events
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.abi_service = ABIEventService()

    def _normalize_adjacent_arrays_file(self, abi_file: str) -> str:
        """Normalize files that contain multiple adjacent JSON values (e.g., `[...][...]`).
        If multiple top-level arrays are found, merge them into a single array and write to a temp file.
        Return the path to use for further processing.
        """
        try:
            with open(abi_file, "r", encoding="utf-8") as r:
                content = r.read()

            # Fast path: already valid single JSON value
            try:
                value = json.loads(content)
                # If it's already a single list, no change needed
                return abi_file
            except Exception:
                pass

            # Streaming parse multiple top-level JSON values
            decoder = json.JSONDecoder()
            idx = 0
            length = len(content)
            values = []
            
            # Parse each block [...]
            while True:
                # Skip whitespace
                while idx < length and content[idx].isspace():
                    idx += 1
                if idx >= length:
                    break
                try:
                    value, next_idx = decoder.raw_decode(content, idx)
                    values.append(value)
                    idx = next_idx
                except json.JSONDecodeError:
                    # If we fail here, abort normalization
                    values = []
                    break

            # If we parsed multiple values and they are arrays, merge
            if len(values) >= 2 and all(isinstance(v, list) for v in values):
                merged = []
                for v in values:
                    merged.extend(v)
                tmp = tempfile.NamedTemporaryFile("w", delete=False, suffix=".json")
                with tmp as w:
                    json.dump(merged, w, ensure_ascii=False)
                self.logger.info(f"Normalized adjacent arrays into a single array: {tmp.name}")
                return tmp.name

            # If a single value that is not a list, leave as-is
            return abi_file
        except Exception as e:
            self.logger.warning(f"Normalization skipped due to error: {e}")
            return abi_file

    def extract_events(self, abi_file: str, target_file: str, force: bool = False) -> Dict[str, Any]:
        """
        Extract events from ABI file and save to target file

        Args:
            abi_file: Path to source ABI JSON file
            target_file: Path to target file to save events
            force: Force overwrite existing events (disable unique check)

        Returns:
            Dictionary with extraction results
        """
        try:
            self.logger.info(f"Extracting events from {abi_file} to {target_file}")

            # Normalize input if it contains adjacent arrays
            source_path = self._normalize_adjacent_arrays_file(abi_file)

            if force:
                self.logger.info("Force mode: Unique check disabled")
                # Load ABI and extract events
                abi_data = self.abi_service.load_abi_from_file(source_path)
                new_events = self.abi_service.extract_events_from_abi(abi_data)
                self.abi_service.save_events_to_file(target_file, new_events)
                self.logger.info(f"Force saved {len(new_events)} events to {target_file}")
            else:
                # Extract and save events with uniqueness check
                self.abi_service.extract_and_save_events(source_path, target_file)

            # Get summary
            summary = self.abi_service.get_events_summary(target_file)

            return {"success": True, "summary": summary, "abi_file": abi_file, "target_file": target_file}

        except Exception as e:
            self.logger.error(f"Error extracting events: {e}")
            return {"success": False, "error": str(e), "abi_file": abi_file, "target_file": target_file}

    def get_summary(self, target_file: str) -> Dict[str, Any]:
        """
        Get summary of events in target file

        Args:
            target_file: Path to file containing events

        Returns:
            Dictionary with event summary
        """
        try:
            summary = self.abi_service.get_events_summary(target_file)
            return {"success": True, "summary": summary, "target_file": target_file}
        except Exception as e:
            self.logger.error(f"Error getting summary: {e}")
            return {"success": False, "error": str(e), "target_file": target_file}
