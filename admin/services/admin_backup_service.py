"""
Admin backup service for Firebase data.
"""

import logging
import json
import zipfile
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
from admin.config.admin_config import admin_config
from admin.utils.constants import (
    FIRESTORE_USER_LICENSES_COLLECTION,
    FIRESTORE_LICENSE_TIERS_COLLECTION,
    FIRESTORE_APP_UPDATES_COLLECTION,
    FIRESTORE_NOTIFICATIONS_COLLECTION,
    FIRESTORE_USER_NOTIFICATIONS_COLLECTION,
    FIRESTORE_SCHEDULED_DELETIONS_COLLECTION,
    FIRESTORE_USER_ACTIVITIES_COLLECTION,
)

logger = logging.getLogger(__name__)


class AdminBackupService:
    """Handles Firebase data backup operations."""
    
    def __init__(self):
        self._db = None
        self._auth = None
    
    def _ensure_initialized(self) -> bool:
        """Ensure Firebase is initialized."""
        if not admin_config.is_initialized():
            if not admin_config.initialize():
                return False
        self._db = admin_config.get_firestore()
        self._auth = admin_config.get_auth()
        return self._db is not None and self._auth is not None
    
    def _serialize_timestamp(self, obj: Any) -> Any:
        """Convert Firestore timestamps and other objects to JSON-serializable format."""
        if obj is None:
            return None
        
        # Handle Firestore timestamps
        if hasattr(obj, 'timestamp'):
            # Firestore timestamp
            try:
                dt = obj.to_datetime()
                return dt.isoformat() + "Z"
            except Exception:
                return str(obj)
        
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat() + "Z"
        
        # Handle lists
        if isinstance(obj, list):
            return [self._serialize_timestamp(item) for item in obj]
        
        # Handle dictionaries
        if isinstance(obj, dict):
            return {key: self._serialize_timestamp(value) for key, value in obj.items()}
        
        # Handle other types that might not be JSON serializable
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)
    
    def _backup_firestore_collection(self, collection_name: str) -> List[dict]:
        """Backup a Firestore collection."""
        if not self._ensure_initialized():
            logger.error(f"Firebase not initialized, cannot backup {collection_name}")
            return []
        
        try:
            docs = []
            collection_ref = self._db.collection(collection_name)
            
            for doc in collection_ref.stream():
                data = doc.to_dict()
                if data is None:
                    data = {}
                
                # Add document ID
                data["_id"] = doc.id
                
                # Serialize timestamps
                data = self._serialize_timestamp(data)
                
                docs.append(data)
            
            logger.info(f"Backed up {len(docs)} documents from {collection_name}")
            return docs
            
        except Exception as e:
            logger.error(f"Error backing up collection {collection_name}: {e}", exc_info=True)
            return []
    
    def _backup_subcollection(
        self, 
        parent_collection: str, 
        subcollection_name: str
    ) -> List[dict]:
        """Backup a subcollection from all parent documents."""
        if not self._ensure_initialized():
            logger.error(f"Firebase not initialized, cannot backup subcollection {subcollection_name}")
            return []
        
        try:
            all_subdocs = []
            
            # Get all parent documents
            parent_docs = self._db.collection(parent_collection).stream()
            
            for parent_doc in parent_docs:
                parent_id = parent_doc.id
                
                # Get subcollection
                subcollection_ref = (
                    self._db.collection(parent_collection)
                    .document(parent_id)
                    .collection(subcollection_name)
                )
                
                # Get all documents in subcollection
                for subdoc in subcollection_ref.stream():
                    data = subdoc.to_dict()
                    if data is None:
                        data = {}
                    
                    # Add IDs
                    data["_id"] = subdoc.id
                    data["_parent_id"] = parent_id
                    
                    # Serialize timestamps
                    data = self._serialize_timestamp(data)
                    
                    all_subdocs.append(data)
            
            logger.info(
                f"Backed up {len(all_subdocs)} documents from {parent_collection}/*/{subcollection_name}"
            )
            return all_subdocs
            
        except Exception as e:
            logger.error(
                f"Error backing up subcollection {parent_collection}/*/{subcollection_name}: {e}",
                exc_info=True
            )
            return []
    
    def _backup_firebase_auth_users(self) -> List[dict]:
        """Backup Firebase Auth users."""
        if not self._ensure_initialized():
            logger.error("Firebase not initialized, cannot backup Auth users")
            return []
        
        if self._auth is None:
            logger.error("Firebase Auth is None, cannot backup Auth users")
            return []
        
        try:
            users = []
            logger.debug("Starting Firebase Auth users backup...")
            
            # Try using admin_user_service first (known to work)
            try:
                from admin.services.admin_user_service import admin_user_service
                logger.debug("Attempting to use admin_user_service.get_all_users() as fallback")
                user_list = admin_user_service.get_all_users()
                
                if user_list:
                    logger.info(f"Retrieved {len(user_list)} users via admin_user_service")
                    # Transform to backup format
                    for user_data in user_list:
                        backup_user = {
                            "_id": user_data.get("uid"),
                            "uid": user_data.get("uid"),
                            "email": user_data.get("email"),
                            "display_name": user_data.get("display_name"),
                            "email_verified": user_data.get("email_verified"),
                            "disabled": user_data.get("disabled"),
                            "phone_number": None,  # Not available from admin_user_service
                            "created_at": self._serialize_timestamp(user_data.get("created_at")),
                            "last_sign_in": self._serialize_timestamp(user_data.get("last_sign_in")),
                            "custom_claims": None,  # Not available from admin_user_service
                            "provider_data": [],  # Not available from admin_user_service
                        }
                        users.append(backup_user)
                    
                    logger.info(f"Backed up {len(users)} Firebase Auth users via admin_user_service")
                    return users
                else:
                    logger.warning("admin_user_service returned empty list, trying direct method")
            except Exception as fallback_error:
                logger.warning(f"Fallback to admin_user_service failed: {fallback_error}, trying direct method")
            
            # Direct method (original approach)
            try:
                page = self._auth.list_users()
                logger.debug(f"Got list_users page object: {type(page)}")
            except Exception as e:
                logger.error(f"Error calling list_users(): {e}", exc_info=True)
                return users if users else []
            
            # Iterate through all users
            try:
                user_count = 0
                for user in page.iterate_all():
                    user_count += 1
                    try:
                        user_dict = {
                            "_id": user.uid,
                            "uid": user.uid,
                            "email": user.email if user.email else None,
                            "display_name": user.display_name if user.display_name else None,
                            "email_verified": user.email_verified if hasattr(user, 'email_verified') else None,
                            "disabled": user.disabled if hasattr(user, 'disabled') else None,
                            "phone_number": user.phone_number if user.phone_number else None,
                        }
                        
                        # Handle metadata
                        if hasattr(user, 'user_metadata') and user.user_metadata:
                            if user.user_metadata.creation_timestamp:
                                try:
                                    user_dict["created_at"] = user.user_metadata.creation_timestamp.isoformat() + "Z"
                                except Exception:
                                    user_dict["created_at"] = str(user.user_metadata.creation_timestamp)
                            else:
                                user_dict["created_at"] = None
                            
                            if user.user_metadata.last_sign_in_timestamp:
                                try:
                                    user_dict["last_sign_in"] = user.user_metadata.last_sign_in_timestamp.isoformat() + "Z"
                                except Exception:
                                    user_dict["last_sign_in"] = str(user.user_metadata.last_sign_in_timestamp)
                            else:
                                user_dict["last_sign_in"] = None
                        else:
                            user_dict["created_at"] = None
                            user_dict["last_sign_in"] = None
                        
                        # Handle custom claims
                        if hasattr(user, 'custom_claims') and user.custom_claims:
                            user_dict["custom_claims"] = user.custom_claims
                        else:
                            user_dict["custom_claims"] = None
                        
                        # Handle provider data
                        if hasattr(user, 'provider_data') and user.provider_data:
                            user_dict["provider_data"] = [
                                {
                                    "uid": pd.uid if hasattr(pd, 'uid') else None,
                                    "email": pd.email if hasattr(pd, 'email') else None,
                                    "display_name": pd.display_name if hasattr(pd, 'display_name') else None,
                                    "photo_url": pd.photo_url if hasattr(pd, 'photo_url') else None,
                                    "provider_id": pd.provider_id if hasattr(pd, 'provider_id') else None,
                                }
                                for pd in user.provider_data
                            ]
                        else:
                            user_dict["provider_data"] = []
                        
                        users.append(user_dict)
                        logger.debug(f"Processed user {user_count}: {user.uid}")
                        
                    except Exception as user_error:
                        logger.warning(f"Error processing user {user.uid if hasattr(user, 'uid') else 'unknown'}: {user_error}", exc_info=True)
                        # Continue with next user
                        continue
                
                logger.info(f"Backed up {len(users)} Firebase Auth users (processed {user_count} total via direct method)")
                
            except StopIteration:
                logger.info(f"Finished iterating users. Backed up {len(users)} Firebase Auth users")
            except Exception as iter_error:
                logger.error(f"Error during user iteration: {iter_error}", exc_info=True)
                # Return what we have so far
                if users:
                    logger.warning(f"Returning {len(users)} users that were successfully backed up before error")
            
            if not users:
                logger.warning("No Firebase Auth users were backed up. This might indicate:")
                logger.warning("  1. There are no users in Firebase Auth")
                logger.warning("  2. There's an authentication/permissions issue")
                logger.warning("  3. The Firebase Admin SDK is not properly configured")
            
            return users
            
        except Exception as e:
            logger.error(f"Error backing up Firebase Auth users: {e}", exc_info=True)
            return []
    
    def _create_backup_metadata(self, collections_data: Dict[str, List[dict]]) -> dict:
        """Create backup metadata."""
        metadata = {
            "backup_timestamp": datetime.utcnow().isoformat() + "Z",
            "backup_version": "1.0",
            "collections": {},
            "errors": [],
        }
        
        for collection_name, data in collections_data.items():
            status = "success"
            if data is None:
                status = "error"
                metadata["errors"].append(f"Failed to backup {collection_name}")
            
            metadata["collections"][collection_name] = {
                "count": len(data) if data else 0,
                "status": status,
            }
        
        return metadata
    
    def _create_zip_file(
        self, 
        data_files: Dict[str, List[dict]], 
        output_path: str
    ) -> bool:
        """Create ZIP file with all backup data."""
        try:
            output_path = Path(output_path)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add each collection as a JSON file
                for collection_name, data in data_files.items():
                    if data is None:
                        # Create empty array for failed collections
                        data = []
                    
                    json_content = json.dumps(data, indent=2, ensure_ascii=False)
                    json_filename = f"{collection_name}.json"
                    zipf.writestr(json_filename, json_content.encode('utf-8'))
                    logger.debug(f"Added {json_filename} to backup ZIP")
            
            logger.info(f"Created backup ZIP file: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating ZIP file: {e}", exc_info=True)
            return False
    
    def backup_all_collections(
        self, 
        output_path: str,
        progress_callback: Optional[Any] = None
    ) -> Tuple[bool, dict]:
        """
        Backup all Firebase collections and Auth users to a ZIP file.
        
        Args:
            output_path: Path to save the backup ZIP file
            progress_callback: Optional callback function(collection_name, status)
        
        Returns:
            Tuple of (success: bool, metadata: dict)
        """
        if not self._ensure_initialized():
            logger.error("Firebase not initialized, cannot perform backup")
            return False, {}
        
        logger.info("Starting Firebase backup...")
        
        collections_data = {}
        all_collections = [
            ("firebase_auth_users", self._backup_firebase_auth_users),
            (FIRESTORE_USER_LICENSES_COLLECTION, lambda: self._backup_firestore_collection(FIRESTORE_USER_LICENSES_COLLECTION)),
            ("user_devices", lambda: self._backup_subcollection(FIRESTORE_USER_LICENSES_COLLECTION, "user_devices")),
            (FIRESTORE_LICENSE_TIERS_COLLECTION, lambda: self._backup_firestore_collection(FIRESTORE_LICENSE_TIERS_COLLECTION)),
            (FIRESTORE_APP_UPDATES_COLLECTION, lambda: self._backup_firestore_collection(FIRESTORE_APP_UPDATES_COLLECTION)),
            (FIRESTORE_NOTIFICATIONS_COLLECTION, lambda: self._backup_firestore_collection(FIRESTORE_NOTIFICATIONS_COLLECTION)),
            ("user_notifications", lambda: self._backup_subcollection(FIRESTORE_USER_NOTIFICATIONS_COLLECTION, "notifications")),
            (FIRESTORE_SCHEDULED_DELETIONS_COLLECTION, lambda: self._backup_firestore_collection(FIRESTORE_SCHEDULED_DELETIONS_COLLECTION)),
            (FIRESTORE_USER_ACTIVITIES_COLLECTION, lambda: self._backup_firestore_collection(FIRESTORE_USER_ACTIVITIES_COLLECTION)),
        ]
        
        # Backup each collection
        for collection_name, backup_func in all_collections:
            if progress_callback:
                progress_callback(collection_name, "starting")
            
            try:
                data = backup_func()
                collections_data[collection_name] = data
                
                if progress_callback:
                    progress_callback(collection_name, "completed")
                    
            except Exception as e:
                logger.error(f"Error backing up {collection_name}: {e}", exc_info=True)
                collections_data[collection_name] = None
                
                if progress_callback:
                    progress_callback(collection_name, "error")
        
        # Create metadata
        metadata = self._create_backup_metadata(collections_data)
        collections_data["backup_metadata"] = [metadata]
        
        # Create ZIP file
        if progress_callback:
            progress_callback("backup_metadata", "creating_zip")
        
        success = self._create_zip_file(collections_data, output_path)
        
        if success:
            logger.info(f"Backup completed successfully: {output_path}")
            if progress_callback:
                progress_callback("backup_metadata", "completed")
        else:
            logger.error("Failed to create backup ZIP file")
            if progress_callback:
                progress_callback("backup_metadata", "error")
        
        return success, metadata


# Global admin backup service instance
admin_backup_service = AdminBackupService()

