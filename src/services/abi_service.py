"""
Service for extracting and managing ABI events
"""

import json
import logging
from typing import List, Dict, Any, Set
from pathlib import Path


class ABIEventService:
    """
    Service class for extracting events from ABI JSON files
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_events_from_abi(self, abi_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract all events from ABI data

        Args:
            abi_data: List of ABI function/event definitions

        Returns:
            List of event definitions
        """
        events = []
        
        for item in abi_data:
            if item.get("type") == "event":
                events.append(item)
                self.logger.debug(f"Found event: {item.get('name', 'Unknown')}")
        
        self.logger.info(f"Extracted {len(events)} events from ABI")
        return events

    def load_abi_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load ABI data from JSON file

        Args:
            file_path: Path to the ABI JSON file

        Returns:
            List of ABI definitions
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                abi_data = json.load(file)
            
            self.logger.info(f"Successfully loaded ABI from {file_path}")
            return abi_data
            
        except FileNotFoundError:
            self.logger.error(f"ABI file not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in ABI file {file_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading ABI file {file_path}: {e}")
            raise

    def load_target_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load target file (e.g., lista.json) to update with events

        Args:
            file_path: Path to the target file

        Returns:
            Dictionary containing the file data
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            self.logger.info(f"Successfully loaded target file: {file_path}")
            return data
            
        except FileNotFoundError:
            self.logger.warning(f"Target file not found: {file_path}. Creating new structure.")
            return {"_id": Path(file_path).stem, "addresses": {}, "event_abi": []}
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in target file {file_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading target file {file_path}: {e}")
            raise

    def get_event_signature(self, event: Dict[str, Any]) -> str:
        """
        Generate unique signature for an event based on its name and inputs

        Args:
            event: Event definition

        Returns:
            Unique signature string
        """
        name = event.get("name", "")
        inputs = event.get("inputs", [])
        
        # Create signature based on name and input types
        input_types = []
        for input_param in inputs:
            input_types.append(input_param.get("type", ""))
        
        signature = f"{name}({','.join(input_types)})"
        return signature

    def merge_events_with_unique_check(self, existing_events: List[Dict[str, Any]], 
                                     new_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge new events with existing events, ensuring uniqueness

        Args:
            existing_events: List of existing events
            new_events: List of new events to add

        Returns:
            List of merged unique events
        """
        # Create set of existing event signatures for quick lookup
        existing_signatures: Set[str] = set()
        for event in existing_events:
            signature = self.get_event_signature(event)
            existing_signatures.add(signature)

        # Add new events that don't already exist
        merged_events = existing_events.copy()
        added_count = 0
        
        for event in new_events:
            signature = self.get_event_signature(event)
            if signature not in existing_signatures:
                merged_events.append(event)
                existing_signatures.add(signature)
                added_count += 1
                self.logger.debug(f"Added new event: {event.get('name', 'Unknown')}")
            else:
                self.logger.debug(f"Skipped duplicate event: {event.get('name', 'Unknown')}")

        self.logger.info(f"Added {added_count} new unique events. Total events: {len(merged_events)}")
        return merged_events

    def save_events_to_file(self, target_file_path: str, events: List[Dict[str, Any]]) -> None:
        """
        Save events to target file

        Args:
            target_file_path: Path to save the events
            events: List of events to save
        """
        try:
            # Load existing file data
            file_data = self.load_target_file(target_file_path)
            
            # Update event_abi field
            file_data["event_abi"] = events
            
            # Save updated data
            with open(target_file_path, 'w', encoding='utf-8') as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)
            
            self.logger.info(f"Successfully saved {len(events)} events to {target_file_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving events to file {target_file_path}: {e}")
            raise

    def extract_and_save_events(self, abi_file_path: str, target_file_path: str) -> None:
        """
        Main method to extract events from ABI file and save to target file

        Args:
            abi_file_path: Path to source ABI JSON file
            target_file_path: Path to target file to save events
        """
        try:
            # Load ABI data
            abi_data = self.load_abi_from_file(abi_file_path)
            
            # Extract events
            new_events = self.extract_events_from_abi(abi_data)
            
            # Load target file
            target_data = self.load_target_file(target_file_path)
            existing_events = target_data.get("event_abi", [])
            
            # Merge events with uniqueness check
            merged_events = self.merge_events_with_unique_check(existing_events, new_events)
            
            # Save updated events
            self.save_events_to_file(target_file_path, merged_events)
            
            self.logger.info(f"Successfully processed events from {abi_file_path} to {target_file_path}")
            
        except Exception as e:
            self.logger.error(f"Error in extract_and_save_events: {e}")
            raise

    def get_events_summary(self, file_path: str) -> Dict[str, Any]:
        """
        Get summary of events in a file

        Args:
            file_path: Path to file containing events

        Returns:
            Dictionary with event summary
        """
        try:
            data = self.load_target_file(file_path)
            events = data.get("event_abi", [])
            
            summary = {
                "total_events": len(events),
                "event_names": [event.get("name", "Unknown") for event in events],
                "unique_signatures": len(set(self.get_event_signature(event) for event in events))
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting events summary from {file_path}: {e}")
            raise
