"""
Generic Firestore real-time watch service using REST API Watch Streams.
"""

import logging
import asyncio
import json
import uuid
from typing import Optional, Callable, Dict, List, Any
from datetime import datetime

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logging.warning("httpx library not installed - real-time listeners will not work")

from utils.constants import FIREBASE_PROJECT_ID
from services.auth_service import auth_service

logger = logging.getLogger(__name__)

# Import configuration flag
try:
    from config.settings import ENABLE_REALTIME_WATCH_SERVICES
except ImportError:
    # Fallback if settings not available
    ENABLE_REALTIME_WATCH_SERVICES = False

FIRESTORE_WATCH_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents:watch"


class FirestoreWatchService:
    """
    Generic Firestore watch service for real-time document updates.
    Uses Firestore REST API Watch Streams with HTTP/2.
    """
    
    def __init__(self):
        """Initialize watch service."""
        self.project_id = FIREBASE_PROJECT_ID
        self._listeners: Dict[str, Dict[str, Any]] = {}
        self._client: Optional[httpx.AsyncClient] = None
        
        # Check if watch services are enabled via configuration
        if not ENABLE_REALTIME_WATCH_SERVICES:
            self._is_available = False
            logger.info("Real-time watch services disabled via configuration (ENABLE_REALTIME_WATCH_SERVICES=False)")
            return
        
        self._is_available = HTTPX_AVAILABLE
        
        if not self._is_available:
            logger.warning("httpx not available - real-time listeners disabled")
    
    def _get_id_token(self) -> Optional[str]:
        """
        Get current ID token from auth service or firebase config.
        
        Returns:
            ID token string or None
        """
        try:
            # Try to get from firebase_config first
            from config.firebase_config import firebase_config
            if hasattr(firebase_config, '_current_id_token'):
                token = firebase_config._current_id_token
                if token:
                    return token
            
            # Fallback: check if auth_service has current user with token
            if auth_service.current_user:
                # Token should be stored in firebase_config
                return firebase_config._current_id_token if hasattr(firebase_config, '_current_id_token') else None
            
            logger.warning("No ID token available for watch stream")
            return None
        except Exception as e:
            logger.error(f"Error getting ID token: {e}")
            return None
    
    def _parse_firestore_document(self, doc: dict) -> Optional[dict]:
        """
        Parse Firestore document format to Python dict.
        
        Args:
            doc: Firestore document from API
            
        Returns:
            Parsed document dict or None
        """
        try:
            if "name" not in doc:
                return None
            
            # Extract document ID from name path
            doc_name = doc.get("name", "")
            doc_id = doc_name.split("/")[-1] if "/" in doc_name else ""
            
            # Parse fields
            fields = doc.get("fields", {})
            parsed = {"document_id": doc_id}
            
            for key, value in fields.items():
                if "stringValue" in value:
                    parsed[key] = value["stringValue"]
                elif "integerValue" in value:
                    parsed[key] = int(value["integerValue"])
                elif "doubleValue" in value:
                    parsed[key] = float(value["doubleValue"])
                elif "booleanValue" in value:
                    parsed[key] = value["booleanValue"]
                elif "timestampValue" in value:
                    parsed[key] = value["timestampValue"]
                elif "arrayValue" in value:
                    array_values = value["arrayValue"].get("values", [])
                    parsed[key] = [
                        v.get("stringValue", "") if "stringValue" in v else
                        v.get("integerValue", 0) if "integerValue" in v else
                        v.get("doubleValue", 0.0) if "doubleValue" in v else
                        v.get("booleanValue", False) if "booleanValue" in v else
                        str(v)
                        for v in array_values
                    ]
                elif "mapValue" in value:
                    map_fields = value["mapValue"].get("fields", {})
                    parsed[key] = self._parse_firestore_document({"fields": map_fields})
                elif "nullValue" in value:
                    parsed[key] = None
                else:
                    parsed[key] = str(value)
            
            return parsed
        except Exception as e:
            logger.error(f"Error parsing Firestore document: {e}", exc_info=True)
            return None
    
    def _build_query_filter(self, filters: List[dict]) -> Optional[dict]:
        """
        Build Firestore query filter from filter list.
        
        Args:
            filters: List of filter dicts with keys: field, op, value
            
        Returns:
            Firestore structured query filter or None
        """
        if not filters:
            return None
        
        # For now, support simple field filters
        # Can be extended for more complex queries
        if len(filters) == 1:
            filter_item = filters[0]
            field = filter_item.get("field")
            op = filter_item.get("op", "EQUAL")
            value = filter_item.get("value")
            
            if not field or value is None:
                return None
            
            # Map operation to Firestore op
            op_map = {
                "EQUAL": "EQUAL",
                "NOT_EQUAL": "NOT_EQUAL",
                "GREATER_THAN": "GREATER_THAN",
                "GREATER_THAN_OR_EQUAL": "GREATER_THAN_OR_EQUAL",
                "LESS_THAN": "LESS_THAN",
                "LESS_THAN_OR_EQUAL": "LESS_THAN_OR_EQUAL",
                "ARRAY_CONTAINS": "ARRAY_CONTAINS",
            }
            
            firestore_op = op_map.get(op, "EQUAL")
            
            # Convert value to Firestore value format
            if isinstance(value, str):
                value_obj = {"stringValue": value}
            elif isinstance(value, int):
                value_obj = {"integerValue": str(value)}
            elif isinstance(value, float):
                value_obj = {"doubleValue": value}
            elif isinstance(value, bool):
                value_obj = {"booleanValue": value}
            else:
                value_obj = {"stringValue": str(value)}
            
            return {
                "fieldFilter": {
                    "field": {"fieldPath": field},
                    "op": firestore_op,
                    "value": value_obj
                }
            }
        
        # Multiple filters - use composite filter (AND)
        filter_list = []
        for filter_item in filters:
            single_filter = self._build_query_filter([filter_item])
            if single_filter:
                filter_list.append(single_filter)
        
        if filter_list:
            return {
                "compositeFilter": {
                    "op": "AND",
                    "filters": filter_list
                }
            }
        
        return None
    
    async def watch_collection(
        self,
        collection_path: str,
        on_added: Callable[[dict], None],
        on_updated: Optional[Callable[[dict], None]] = None,
        on_deleted: Optional[Callable[[str], None]] = None,
        filters: Optional[List[dict]] = None,
        id_token: Optional[str] = None
    ) -> str:
        """
        Watch a Firestore collection for real-time updates.
        
        Args:
            collection_path: Collection path (e.g., "notifications")
            on_added: Callback when document is added (receives document dict)
            on_updated: Optional callback when document is updated (receives document dict)
            on_deleted: Optional callback when document is deleted (receives document_id)
            filters: Optional list of query filters [{"field": "name", "op": "EQUAL", "value": "test"}]
            id_token: Optional ID token (uses current token if not provided)
            
        Returns:
            Listener ID string for managing this listener
        """
        if not self._is_available:
            logger.error("httpx not available - cannot start watch stream")
            return ""
        
        listener_id = str(uuid.uuid4())
        id_token = id_token or self._get_id_token()
        
        if not id_token:
            logger.error("No ID token available for watch stream")
            return ""
        
        # Create watch target
        structured_query = {
            "from": [{"collectionId": collection_path}]
        }
        
        # Add filters if provided
        if filters:
            query_filter = self._build_query_filter(filters)
            if query_filter:
                structured_query["where"] = query_filter
        
        target = {
            "query": {
                "parent": f"projects/{self.project_id}/databases/(default)/documents",
                "structuredQuery": structured_query
            }
        }
        
        # Store listener info
        self._listeners[listener_id] = {
            "collection_path": collection_path,
            "on_added": on_added,
            "on_updated": on_updated,
            "on_deleted": on_deleted,
            "task": None,
            "active": False
        }
        
        # Start watch task
        task = asyncio.create_task(
            self._watch_stream(listener_id, target, id_token)
        )
        self._listeners[listener_id]["task"] = task
        
        logger.info(f"Started watch stream for collection '{collection_path}' (listener_id: {listener_id})")
        return listener_id
    
    async def watch_document(
        self,
        document_path: str,
        on_updated: Callable[[dict], None],
        id_token: Optional[str] = None
    ) -> str:
        """
        Watch a specific Firestore document for real-time updates.
        
        Args:
            document_path: Full document path (e.g., "app_updates/latest")
            on_updated: Callback when document is updated (receives document dict)
            id_token: Optional ID token (uses current token if not provided)
            
        Returns:
            Listener ID string for managing this listener
        """
        if not self._is_available:
            logger.error("httpx not available - cannot start watch stream")
            return ""
        
        listener_id = str(uuid.uuid4())
        id_token = id_token or self._get_id_token()
        
        if not id_token:
            logger.error("No ID token available for watch stream")
            return ""
        
        # Create watch target for specific document
        target = {
            "documents": {
                "documents": [f"projects/{self.project_id}/databases/(default)/documents/{document_path}"]
            }
        }
        
        # Store listener info
        self._listeners[listener_id] = {
            "document_path": document_path,
            "on_updated": on_updated,
            "task": None,
            "active": False
        }
        
        # Start watch task
        task = asyncio.create_task(
            self._watch_stream(listener_id, target, id_token)
        )
        self._listeners[listener_id]["task"] = task
        
        logger.info(f"Started watch stream for document '{document_path}' (listener_id: {listener_id})")
        return listener_id
    
    async def _watch_stream(self, listener_id: str, target: dict, id_token: str):
        """
        Internal method to handle watch stream connection.
        
        Args:
            listener_id: Unique listener identifier
            target: Watch target configuration
            id_token: Firebase ID token
        """
        listener = self._listeners.get(listener_id)
        if not listener:
            logger.error(f"Listener {listener_id} not found")
            return
        
        listener["active"] = True
        max_retries = 3
        retry_count = 0
        backoff_seconds = 1
        
        while retry_count < max_retries and listener["active"]:
            try:
                headers = {
                    "Authorization": f"Bearer {id_token}",
                    "Content-Type": "application/json"
                }
                
                body = {
                    "database": f"projects/{self.project_id}/databases/(default)",
                    "addTarget": target
                }
                
                # Use httpx for HTTP/2 streaming
                async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
                    async with client.stream("POST", FIRESTORE_WATCH_URL, headers=headers, json=body) as response:
                        if response.status_code != 200:
                            # Read response content before accessing .text for streaming responses
                            try:
                                error_text = await response.aread()
                                error_message = error_text.decode('utf-8') if error_text else "No error message"
                            except Exception as e:
                                error_message = f"Error reading response: {e}"
                            logger.error(f"Watch stream error: {response.status_code} - {error_message}")
                            retry_count += 1
                            if retry_count < max_retries:
                                await asyncio.sleep(backoff_seconds)
                                backoff_seconds *= 2  # Exponential backoff
                            continue
                        
                        # Reset retry count on successful connection
                        retry_count = 0
                        backoff_seconds = 1
                        
                        logger.debug(f"Watch stream connected for listener {listener_id}")
                        
                        async for line in response.aiter_lines():
                            if not listener["active"]:
                                break
                            
                            if not line.strip():
                                continue
                            
                            try:
                                data = json.loads(line)
                                await self._process_watch_response(listener_id, data, id_token)
                            except json.JSONDecodeError:
                                continue
                            except Exception as e:
                                logger.error(f"Error processing watch stream line: {e}")
                
            except asyncio.CancelledError:
                logger.info(f"Watch stream cancelled for listener {listener_id}")
                break
            except Exception as e:
                logger.error(f"Error in watch stream for listener {listener_id}: {e}", exc_info=True)
                retry_count += 1
                if retry_count < max_retries and listener["active"]:
                    await asyncio.sleep(backoff_seconds)
                    backoff_seconds *= 2
                else:
                    logger.error(f"Max retries reached for listener {listener_id}")
                    break
        
        listener["active"] = False
        logger.info(f"Watch stream stopped for listener {listener_id}")
    
    async def _process_watch_response(self, listener_id: str, data: dict, id_token: str):
        """
        Process watch stream response and trigger callbacks.
        
        Args:
            listener_id: Listener identifier
            data: Watch response data
            id_token: Firebase ID token (for reconnection if needed)
        """
        listener = self._listeners.get(listener_id)
        if not listener:
            return
        
        try:
            # Handle target change (connection status)
            if "targetChange" in data:
                change = data["targetChange"]
                change_type = change.get("targetChangeType")
                
                if change_type == "REMOVE":
                    logger.warning(f"Watch target removed for listener {listener_id}, will reconnect")
                    # The stream will reconnect automatically
                elif change_type == "CURRENT":
                    logger.debug(f"Watch stream current for listener {listener_id}")
                elif change_type == "RESET":
                    logger.info(f"Watch stream reset for listener {listener_id}")
            
            # Handle document changes
            elif "documentChange" in data:
                change = data["documentChange"]
                doc = change.get("document")
                
                if not doc:
                    return
                
                parsed_doc = self._parse_firestore_document(doc)
                if not parsed_doc:
                    return
                
                removed_target_ids = change.get("removedTargetIds", [])
                if removed_target_ids:
                    # Document was removed
                    doc_id = parsed_doc.get("document_id", "")
                    if listener.get("on_deleted"):
                        try:
                            listener["on_deleted"](doc_id)
                        except Exception as e:
                            logger.error(f"Error in on_deleted callback: {e}")
                else:
                    # Document added or updated
                    # Firestore doesn't distinguish between add/update in watch streams
                    # We'll call on_added if it exists, otherwise on_updated
                    if listener.get("on_added"):
                        try:
                            listener["on_added"](parsed_doc)
                        except Exception as e:
                            logger.error(f"Error in on_added callback: {e}")
                    elif listener.get("on_updated"):
                        try:
                            listener["on_updated"](parsed_doc)
                        except Exception as e:
                            logger.error(f"Error in on_updated callback: {e}")
            
            # Handle document delete
            elif "documentDelete" in data:
                delete_data = data["documentDelete"]
                doc_name = delete_data.get("document", "")
                doc_id = doc_name.split("/")[-1] if "/" in doc_name else ""
                
                if doc_id and listener.get("on_deleted"):
                    try:
                        listener["on_deleted"](doc_id)
                    except Exception as e:
                        logger.error(f"Error in on_deleted callback: {e}")
        
        except Exception as e:
            logger.error(f"Error processing watch response: {e}", exc_info=True)
    
    def stop_listener(self, listener_id: str) -> bool:
        """
        Stop a specific listener.
        
        Args:
            listener_id: Listener ID to stop
            
        Returns:
            True if stopped successfully, False otherwise
        """
        listener = self._listeners.get(listener_id)
        if not listener:
            logger.warning(f"Listener {listener_id} not found")
            return False
        
        listener["active"] = False
        task = listener.get("task")
        if task and not task.done():
            task.cancel()
        
        del self._listeners[listener_id]
        logger.info(f"Stopped listener {listener_id}")
        return True
    
    def stop_all_listeners(self) -> None:
        """Stop all active listeners."""
        listener_ids = list(self._listeners.keys())
        for listener_id in listener_ids:
            self.stop_listener(listener_id)
        logger.info("Stopped all listeners")
    
    def is_listener_active(self, listener_id: str) -> bool:
        """
        Check if a listener is active.
        
        Args:
            listener_id: Listener ID to check
            
        Returns:
            True if active, False otherwise
        """
        listener = self._listeners.get(listener_id)
        return listener.get("active", False) if listener else False
    
    def get_active_listeners(self) -> List[str]:
        """
        Get list of active listener IDs.
        
        Returns:
            List of active listener IDs
        """
        return [
            listener_id
            for listener_id, listener in self._listeners.items()
            if listener.get("active", False)
        ]


# Global watch service instance
firestore_watch_service = FirestoreWatchService()

