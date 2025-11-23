"""
gRPC-based Firestore real-time watch service using google-cloud-firestore.
This provides reliable real-time listeners via gRPC instead of REST API.
"""

import logging
import asyncio
import uuid
from typing import Optional, Callable, Dict, List, Any
from pathlib import Path
import os

try:
    from google.cloud import firestore
    from google.oauth2 import service_account
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    firestore = None
    logging.warning("google-cloud-firestore library not installed - gRPC watch service will not work")

from utils.constants import FIREBASE_PROJECT_ID

logger = logging.getLogger(__name__)

# Import configuration flag
try:
    from config.settings import ENABLE_REALTIME_WATCH_SERVICES
except ImportError:
    # Fallback if settings not available
    ENABLE_REALTIME_WATCH_SERVICES = False


class FirestoreGRPCWatchService:
    """
    gRPC-based Firestore watch service for real-time document updates.
    Uses google-cloud-firestore library with on_snapshot listeners.
    """
    
    def __init__(self, credentials_path: Optional[str] = None, auto_init: bool = False):
        """
        Initialize gRPC watch service.
        
        NOTE: gRPC watch service requires Firebase Admin SDK credentials (service account).
        This should NOT be used in desktop apps for security reasons. Use REST API with user ID tokens instead.
        
        Args:
            credentials_path: Optional path to Firebase service account credentials JSON file
            auto_init: If False, service will not initialize automatically (default for security)
                      Set to True only if you explicitly want to use admin credentials
        """
        self.project_id = FIREBASE_PROJECT_ID
        self._listeners: Dict[str, Dict[str, Any]] = {}
        self._db: Optional[firestore.Client] = None
        self._credentials_path = credentials_path
        
        # Check if watch services are enabled via configuration
        if not ENABLE_REALTIME_WATCH_SERVICES:
            self._is_available = False
            logger.info("Real-time watch services disabled via configuration (ENABLE_REALTIME_WATCH_SERVICES=False)")
            return
        
        self._is_available = GRPC_AVAILABLE
        
        if not self._is_available:
            logger.debug("google-cloud-firestore not available - gRPC watch service disabled")
            return
        
        # Only initialize if explicitly requested (security: don't auto-load admin credentials)
        if auto_init:
            self._initialize_client()
        else:
            logger.debug("gRPC watch service not auto-initialized (requires admin credentials - use REST API with user tokens instead)")
    
    def _find_credentials(self) -> Optional[str]:
        """
        Find Firebase service account credentials file.
        
        SECURITY NOTE: Only looks for explicitly provided credentials.
        Does NOT auto-discover credentials to avoid security issues in desktop apps.
        
        Returns:
            Path to credentials file or None
        """
        # Only use explicitly provided path (security: don't auto-discover admin credentials)
        if self._credentials_path and Path(self._credentials_path).exists():
            return self._credentials_path
        
        # Check environment variable (if explicitly set)
        env_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        if env_path and Path(env_path).exists():
            logger.warning("Using admin credentials from FIREBASE_CREDENTIALS_PATH - not recommended for desktop apps")
            return env_path
        
        return None
    
    def _initialize_client(self) -> bool:
        """
        Initialize Firestore client with service account credentials.
        
        SECURITY WARNING: This requires admin credentials which should NOT be bundled in desktop apps.
        Use REST API with user ID tokens instead for desktop applications.
        
        Returns:
            True if initialized successfully, False otherwise
        """
        if not self._is_available:
            return False
        
        try:
            cred_path = self._find_credentials()
            
            if cred_path:
                logger.warning(f"Initializing Firestore gRPC client with admin credentials: {cred_path}")
                logger.warning("WARNING: Admin credentials should NOT be used in desktop apps for security reasons")
                credentials = service_account.Credentials.from_service_account_file(cred_path)
                self._db = firestore.Client(
                    project=self.project_id,
                    credentials=credentials
                )
                logger.info("Firestore gRPC client initialized successfully")
                return True
            else:
                # Don't try default credentials - require explicit configuration for security
                logger.debug("No admin credentials provided - gRPC watch service will not be available")
                logger.debug("Use REST API with user ID tokens instead (more secure for desktop apps)")
                return False
        except Exception as e:
            logger.error(f"Error initializing Firestore gRPC client: {e}", exc_info=True)
            self._db = None
            return False
    
    def _document_to_dict(self, doc: firestore.DocumentSnapshot) -> dict:
        """
        Convert Firestore document snapshot to Python dict.
        
        Args:
            doc: Firestore document snapshot
            
        Returns:
            Document as dict with document_id
        """
        if not doc.exists:
            return {}
        
        data = doc.to_dict()
        if data is None:
            data = {}
        
        # Add document ID
        data["document_id"] = doc.id
        
        # Convert Firestore types to Python types
        return self._convert_firestore_types(data)
    
    def _convert_firestore_types(self, data: Any) -> Any:
        """
        Recursively convert Firestore types to Python types.
        
        Args:
            data: Data to convert
            
        Returns:
            Converted data
        """
        if isinstance(data, dict):
            return {k: self._convert_firestore_types(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_firestore_types(item) for item in data]
        elif hasattr(data, 'timestamp'):  # Firestore Timestamp
            return data.timestamp()
        elif hasattr(data, 'to_dict'):  # Firestore types with to_dict
            return data.to_dict()
        else:
            return data
    
    def _build_query(self, collection_ref: firestore.CollectionReference, filters: Optional[List[dict]] = None):
        """
        Build Firestore query from filters.
        
        Args:
            collection_ref: Firestore collection reference
            filters: Optional list of filter dicts [{"field": "name", "op": "EQUAL", "value": "test"}]
            
        Returns:
            Firestore query object
        """
        query = collection_ref
        
        if not filters:
            return query
        
        # Apply filters
        for filter_item in filters:
            field = filter_item.get("field")
            op = filter_item.get("op", "EQUAL")
            value = filter_item.get("value")
            
            if not field or value is None:
                continue
            
            # Map operation to Firestore query method
            if op == "EQUAL":
                query = query.where(field, "==", value)
            elif op == "NOT_EQUAL":
                query = query.where(field, "!=", value)
            elif op == "GREATER_THAN":
                query = query.where(field, ">", value)
            elif op == "GREATER_THAN_OR_EQUAL":
                query = query.where(field, ">=", value)
            elif op == "LESS_THAN":
                query = query.where(field, "<", value)
            elif op == "LESS_THAN_OR_EQUAL":
                query = query.where(field, "<=", value)
            elif op == "ARRAY_CONTAINS":
                query = query.where(field, "array_contains", value)
            else:
                logger.warning(f"Unsupported filter operation: {op}, using EQUAL")
                query = query.where(field, "==", value)
        
        return query
    
    async def watch_collection(
        self,
        collection_path: str,
        on_added: Callable[[dict], None],
        on_updated: Optional[Callable[[dict], None]] = None,
        on_deleted: Optional[Callable[[str], None]] = None,
        filters: Optional[List[dict]] = None,
        id_token: Optional[str] = None  # Not used in gRPC, kept for compatibility
    ) -> str:
        """
        Watch a Firestore collection for real-time updates.
        
        Args:
            collection_path: Collection path (e.g., "notifications")
            on_added: Callback when document is added (receives document dict)
            on_updated: Optional callback when document is updated (receives document dict)
            on_deleted: Optional callback when document is deleted (receives document_id)
            filters: Optional list of query filters [{"field": "name", "op": "EQUAL", "value": "test"}]
            id_token: Optional ID token (not used in gRPC, kept for compatibility)
            
        Returns:
            Listener ID string for managing this listener
        """
        if not self._is_available or not self._db:
            logger.error("gRPC watch service not available - cannot start watch stream")
            return ""
        
        listener_id = str(uuid.uuid4())
        
        try:
            # Get collection reference
            collection_ref = self._db.collection(collection_path)
            
            # Build query with filters
            query = self._build_query(collection_ref, filters)
            
            # Track seen documents to distinguish add vs update
            seen_docs: Dict[str, bool] = {}
            
            def on_snapshot(doc_snapshots: List[firestore.DocumentSnapshot], changes: List[firestore.DocumentChange], read_time):
                """Handle snapshot changes."""
                try:
                    # Process changes
                    for change in changes:
                        doc = change.document
                        doc_id = doc.id
                        doc_dict = self._document_to_dict(doc)
                        
                        if change.type == firestore.DocumentChange.Type.ADDED:
                            seen_docs[doc_id] = True
                            if on_added:
                                try:
                                    on_added(doc_dict)
                                except Exception as e:
                                    logger.error(f"Error in on_added callback: {e}", exc_info=True)
                        
                        elif change.type == firestore.DocumentChange.Type.MODIFIED:
                            if doc_id in seen_docs:
                                # Document was already seen, this is an update
                                if on_updated:
                                    try:
                                        on_updated(doc_dict)
                                    except Exception as e:
                                        logger.error(f"Error in on_updated callback: {e}", exc_info=True)
                            else:
                                # Document not seen before, treat as add
                                seen_docs[doc_id] = True
                                if on_added:
                                    try:
                                        on_added(doc_dict)
                                    except Exception as e:
                                        logger.error(f"Error in on_added callback: {e}", exc_info=True)
                        
                        elif change.type == firestore.DocumentChange.Type.REMOVED:
                            seen_docs.pop(doc_id, None)
                            if on_deleted:
                                try:
                                    on_deleted(doc_id)
                                except Exception as e:
                                    logger.error(f"Error in on_deleted callback: {e}", exc_info=True)
                    
                    # Handle documents that were removed from query results
                    current_doc_ids = {doc.id for doc in doc_snapshots}
                    removed_doc_ids = set(seen_docs.keys()) - current_doc_ids
                    for doc_id in removed_doc_ids:
                        seen_docs.pop(doc_id, None)
                        if on_deleted:
                            try:
                                on_deleted(doc_id)
                            except Exception as e:
                                logger.error(f"Error in on_deleted callback: {e}", exc_info=True)
                
                except Exception as e:
                    logger.error(f"Error processing snapshot: {e}", exc_info=True)
            
            # Start listening
            listener_registration = query.on_snapshot(on_snapshot)
            
            # Store listener info
            self._listeners[listener_id] = {
                "collection_path": collection_path,
                "on_added": on_added,
                "on_updated": on_updated,
                "on_deleted": on_deleted,
                "registration": listener_registration,
                "active": True,
                "seen_docs": seen_docs
            }
            
            logger.info(f"Started gRPC watch stream for collection '{collection_path}' (listener_id: {listener_id})")
            return listener_id
        
        except Exception as e:
            logger.error(f"Error starting watch stream for collection '{collection_path}': {e}", exc_info=True)
            return ""
    
    async def watch_document(
        self,
        document_path: str,
        on_updated: Callable[[dict], None],
        id_token: Optional[str] = None  # Not used in gRPC, kept for compatibility
    ) -> str:
        """
        Watch a specific Firestore document for real-time updates.
        
        Args:
            document_path: Full document path (e.g., "app_updates/latest")
            on_updated: Callback when document is updated (receives document dict)
            id_token: Optional ID token (not used in gRPC, kept for compatibility)
            
        Returns:
            Listener ID string for managing this listener
        """
        if not self._is_available or not self._db:
            logger.error("gRPC watch service not available - cannot start watch stream")
            return ""
        
        listener_id = str(uuid.uuid4())
        
        try:
            # Get document reference
            doc_ref = self._db.document(document_path)
            
            def on_snapshot(doc: firestore.DocumentSnapshot):
                """Handle document snapshot."""
                try:
                    if doc.exists:
                        doc_dict = self._document_to_dict(doc)
                        if on_updated:
                            try:
                                on_updated(doc_dict)
                            except Exception as e:
                                logger.error(f"Error in on_updated callback: {e}", exc_info=True)
                    else:
                        # Document was deleted
                        logger.debug(f"Document {document_path} does not exist")
                
                except Exception as e:
                    logger.error(f"Error processing document snapshot: {e}", exc_info=True)
            
            # Start listening
            listener_registration = doc_ref.on_snapshot(on_snapshot)
            
            # Store listener info
            self._listeners[listener_id] = {
                "document_path": document_path,
                "on_updated": on_updated,
                "registration": listener_registration,
                "active": True
            }
            
            logger.info(f"Started gRPC watch stream for document '{document_path}' (listener_id: {listener_id})")
            return listener_id
        
        except Exception as e:
            logger.error(f"Error starting watch stream for document '{document_path}': {e}", exc_info=True)
            return ""
    
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
        
        try:
            # Unsubscribe from Firestore listener
            registration = listener.get("registration")
            if registration:
                registration.unsubscribe()
            
            listener["active"] = False
            del self._listeners[listener_id]
            logger.info(f"Stopped gRPC listener {listener_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping listener {listener_id}: {e}", exc_info=True)
            return False
    
    def stop_all_listeners(self) -> None:
        """Stop all active listeners."""
        listener_ids = list(self._listeners.keys())
        for listener_id in listener_ids:
            self.stop_listener(listener_id)
        logger.info("Stopped all gRPC listeners")
    
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
    
    def is_available(self) -> bool:
        """
        Check if gRPC watch service is available.
        
        Returns:
            True if available, False otherwise
        """
        return self._is_available and self._db is not None


# Global gRPC watch service instance
# NOTE: Not auto-initialized for security (requires admin credentials)
# Desktop apps should use REST API with user ID tokens instead
grpc_watch_service = FirestoreGRPCWatchService(auto_init=False)

