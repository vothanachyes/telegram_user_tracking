"""
Firestore conversion helpers for REST API.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class FirestoreHelpers:
    """Helper methods for converting Firestore REST API format."""
    
    @staticmethod
    def convert_firestore_document(firestore_doc: dict) -> Optional[dict]:
        """
        Convert Firestore REST API document format to Python dict.
        
        Firestore REST API returns documents in a nested format:
        {
            "fields": {
                "field_name": {
                    "stringValue": "value"  # or integerValue, booleanValue, etc.
                }
            }
        }
        """
        if 'fields' not in firestore_doc:
            return None
        
        result = {}
        for field_name, field_value in firestore_doc['fields'].items():
            # Handle different Firestore value types
            if 'stringValue' in field_value:
                result[field_name] = field_value['stringValue']
            elif 'integerValue' in field_value:
                result[field_name] = int(field_value['integerValue'])
            elif 'doubleValue' in field_value:
                result[field_name] = float(field_value['doubleValue'])
            elif 'booleanValue' in field_value:
                result[field_name] = field_value['booleanValue']
            elif 'timestampValue' in field_value:
                # Parse ISO timestamp
                result[field_name] = field_value['timestampValue']
            elif 'arrayValue' in field_value:
                # Handle arrays
                values = field_value['arrayValue'].get('values', [])
                result[field_name] = [
                    FirestoreHelpers.convert_firestore_value(v) for v in values
                ]
            elif 'mapValue' in field_value:
                # Handle nested maps
                result[field_name] = FirestoreHelpers.convert_firestore_document(field_value['mapValue'])
            elif 'nullValue' in field_value:
                # Handle null values
                result[field_name] = None
            else:
                # Unknown type, try to extract value
                logger.warning(f"Unknown Firestore field type for {field_name}: {field_value}")
                result[field_name] = str(field_value)
        
        return result
    
    @staticmethod
    def convert_firestore_value(value: dict) -> Any:
        """Convert a single Firestore value to Python type."""
        if 'stringValue' in value:
            return value['stringValue']
        elif 'integerValue' in value:
            return int(value['integerValue'])
        elif 'doubleValue' in value:
            return float(value['doubleValue'])
        elif 'booleanValue' in value:
            return value['booleanValue']
        elif 'nullValue' in value:
            return None
        else:
            return str(value)
    
    @staticmethod
    def convert_to_firestore_value(value: Any) -> dict:
        """
        Convert Python value to Firestore value format.
        
        Args:
            value: Python value (str, int, float, bool, list, dict, None)
        
        Returns:
            Firestore value dict
        """
        if value is None:
            return {"nullValue": None}
        elif isinstance(value, bool):
            return {"booleanValue": value}
        elif isinstance(value, int):
            return {"integerValue": str(value)}
        elif isinstance(value, float):
            return {"doubleValue": value}
        elif isinstance(value, str):
            # Check if it's a timestamp string
            if value.endswith("Z") and "T" in value:
                return {"timestampValue": value}
            return {"stringValue": value}
        elif isinstance(value, datetime):
            return {"timestampValue": value.isoformat() + "Z"}
        elif isinstance(value, list):
            return {
                "arrayValue": {
                    "values": [FirestoreHelpers.convert_to_firestore_value(v) for v in value]
                }
            }
        elif isinstance(value, dict):
            return {
                "mapValue": {
                    "fields": {k: FirestoreHelpers.convert_to_firestore_value(v) for k, v in value.items()}
                }
            }
        else:
            # Fallback to string
            return {"stringValue": str(value)}

