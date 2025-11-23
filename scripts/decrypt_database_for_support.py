#!/usr/bin/env python3
"""
Database Decryption Script for Support

This script decrypts all encrypted fields in a database and creates a new database
with decrypted data. Used by support staff to decrypt user databases for troubleshooting.

The encryption key is derived from:
- Device information (hostname, machine, system)
- Encryption key hash (stored in app_settings table)

Usage:
    python scripts/decrypt_database_for_support.py <input_db> <output_db> --hostname <hostname> --machine <machine> --system <system>
    python scripts/decrypt_database_for_support.py <input_db> <output_db> --device-info <json_file>
    python scripts/decrypt_database_for_support.py <input_db> <output_db>  # Interactive mode

Requirements:
    pip install cryptography
"""

import json
import sys
import sqlite3
import shutil
import hashlib
import base64
import argparse
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


ENCRYPTION_PREFIX = "ENC:"


def derive_encryption_key(hostname: str, machine: str, system: str, encryption_key_hash: str) -> str:
    """
    Derive encryption key from device information and encryption key hash.
    
    This replicates the exact key derivation process used in BaseDatabaseManager.
    
    Args:
        hostname: Device hostname (platform.node())
        machine: Machine type (platform.machine())
        system: Operating system (platform.system())
        encryption_key_hash: Encryption key hash from app_settings
        
    Returns:
        Base64-encoded encryption key
    """
    device_id = f"{hostname}-{machine}-{system}"
    salt = hashlib.sha256(f"{device_id}-field-encryption".encode()).digest()[:16]
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    
    key_material = f"{device_id}-{encryption_key_hash}".encode()
    key_bytes = kdf.derive(key_material)
    encryption_key = base64.urlsafe_b64encode(key_bytes).decode('utf-8')
    
    return encryption_key


def decrypt_field(value: Optional[str], cipher: Fernet) -> Optional[str]:
    """
    Decrypt a field value.
    
    Args:
        value: Encrypted value with prefix, or plain text
        cipher: Fernet cipher instance
        
    Returns:
        Decrypted plain text value, or None/empty string if input was None/empty
    """
    # Handle None and empty strings
    if value is None:
        return None
    
    if not value or not value.strip():
        return value  # Return empty string as-is
    
    # If not encrypted (no prefix), return as-is
    if not value.startswith(ENCRYPTION_PREFIX):
        return value
    
    try:
        # Remove prefix
        encrypted_str = value[len(ENCRYPTION_PREFIX):]
        
        # Decode from base64
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_str.encode('utf-8'))
        
        # Decrypt
        decrypted_bytes = cipher.decrypt(encrypted_bytes)
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        print(f"Warning: Failed to decrypt field value: {e}")
        return value  # Return original value on error


def get_encryption_key_hash(db_path: str) -> Optional[str]:
    """
    Get encryption key hash from app_settings table.
    
    Args:
        db_path: Path to database file
        
    Returns:
        Encryption key hash, or None if not found
    """
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT encryption_key_hash FROM app_settings WHERE id = 1"
            )
            row = cursor.fetchone()
            if row:
                return row['encryption_key_hash']
            return None
    except Exception as e:
        print(f"Error reading encryption_key_hash: {e}")
        return None


def create_cipher(encryption_key: str) -> Fernet:
    """
    Create Fernet cipher from encryption key.
    
    Args:
        encryption_key: Base64-encoded encryption key
        
    Returns:
        Fernet cipher instance
    """
    # Decode the base64 key
    key_bytes = base64.urlsafe_b64decode(encryption_key.encode('utf-8'))
    
    # Fernet requires exactly 32 bytes
    if len(key_bytes) != 32:
        # Use PBKDF2 to derive a 32-byte key
        salt = hashlib.sha256(b"field_encryption_salt").digest()[:16]
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key_bytes = kdf.derive(encryption_key.encode('utf-8'))
    
    # Create Fernet cipher
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def decrypt_database(input_db: str, output_db: str, hostname: str, machine: str, system: str) -> bool:
    """
    Decrypt all encrypted fields in database and create new database.
    
    Args:
        input_db: Path to encrypted database
        output_db: Path to output decrypted database
        hostname: Device hostname
        machine: Machine type
        system: Operating system
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get encryption key hash from database
        print("Reading encryption key hash from database...")
        encryption_key_hash = get_encryption_key_hash(input_db)
        
        if not encryption_key_hash:
            print("Error: encryption_key_hash not found in database. Encryption may not be enabled.")
            return False
        
        # Derive encryption key
        print("Deriving encryption key from device information...")
        encryption_key = derive_encryption_key(hostname, machine, system, encryption_key_hash)
        
        # Create cipher
        cipher = create_cipher(encryption_key)
        
        # Copy database to output location
        print(f"Copying database from {input_db} to {output_db}...")
        shutil.copy2(input_db, output_db)
        
        # Decrypt all encrypted fields
        print("Decrypting encrypted fields...")
        with sqlite3.connect(output_db) as conn:
            conn.row_factory = sqlite3.Row
            
            # Decrypt telegram_credentials
            print("  - Decrypting telegram_credentials...")
            cursor = conn.execute("SELECT id, phone_number, session_string FROM telegram_credentials")
            rows = cursor.fetchall()
            for row in rows:
                decrypted_phone = decrypt_field(row['phone_number'], cipher)
                decrypted_session = decrypt_field(row['session_string'], cipher)
                
                conn.execute("""
                    UPDATE telegram_credentials 
                    SET phone_number = ?, session_string = ?
                    WHERE id = ?
                """, (decrypted_phone, decrypted_session, row['id']))
            print(f"    Decrypted {len(rows)} credential records")
            
            # Decrypt telegram_users
            print("  - Decrypting telegram_users...")
            cursor = conn.execute("""
                SELECT id, username, first_name, last_name, full_name, phone, bio 
                FROM telegram_users
            """)
            rows = cursor.fetchall()
            for row in rows:
                decrypted_username = decrypt_field(row['username'], cipher)
                decrypted_first_name = decrypt_field(row['first_name'], cipher)
                decrypted_last_name = decrypt_field(row['last_name'], cipher)
                decrypted_full_name = decrypt_field(row['full_name'], cipher)
                decrypted_phone = decrypt_field(row['phone'], cipher)
                decrypted_bio = decrypt_field(row['bio'], cipher)
                
                conn.execute("""
                    UPDATE telegram_users 
                    SET username = ?, first_name = ?, last_name = ?, 
                        full_name = ?, phone = ?, bio = ?
                    WHERE id = ?
                """, (
                    decrypted_username, decrypted_first_name, decrypted_last_name,
                    decrypted_full_name, decrypted_phone, decrypted_bio, row['id']
                ))
            print(f"    Decrypted {len(rows)} user records")
            
            # Decrypt messages
            print("  - Decrypting messages...")
            cursor = conn.execute("SELECT id, content, caption, message_link FROM messages")
            rows = cursor.fetchall()
            for row in rows:
                decrypted_content = decrypt_field(row['content'], cipher)
                decrypted_caption = decrypt_field(row['caption'], cipher)
                decrypted_message_link = decrypt_field(row['message_link'], cipher)
                
                conn.execute("""
                    UPDATE messages 
                    SET content = ?, caption = ?, message_link = ?
                    WHERE id = ?
                """, (decrypted_content, decrypted_caption, decrypted_message_link, row['id']))
            print(f"    Decrypted {len(rows)} message records")
            
            # Decrypt reactions
            print("  - Decrypting reactions...")
            cursor = conn.execute("SELECT id, message_link FROM reactions")
            rows = cursor.fetchall()
            for row in rows:
                decrypted_message_link = decrypt_field(row['message_link'], cipher)
                
                conn.execute("""
                    UPDATE reactions 
                    SET message_link = ?
                    WHERE id = ?
                """, (decrypted_message_link, row['id']))
            print(f"    Decrypted {len(rows)} reaction records")
            
            # Decrypt group_fetch_history
            print("  - Decrypting group_fetch_history...")
            cursor = conn.execute("""
                SELECT id, account_phone_number, account_full_name, account_username 
                FROM group_fetch_history
            """)
            rows = cursor.fetchall()
            for row in rows:
                decrypted_phone = decrypt_field(row['account_phone_number'], cipher)
                decrypted_full_name = decrypt_field(row['account_full_name'], cipher)
                decrypted_username = decrypt_field(row['account_username'], cipher)
                
                conn.execute("""
                    UPDATE group_fetch_history 
                    SET account_phone_number = ?, account_full_name = ?, account_username = ?
                    WHERE id = ?
                """, (decrypted_phone, decrypted_full_name, decrypted_username, row['id']))
            print(f"    Decrypted {len(rows)} group fetch history records")
            
            # Decrypt account_activity_log
            print("  - Decrypting account_activity_log...")
            cursor = conn.execute("SELECT id, phone_number FROM account_activity_log")
            rows = cursor.fetchall()
            for row in rows:
                decrypted_phone = decrypt_field(row['phone_number'], cipher)
                
                conn.execute("""
                    UPDATE account_activity_log 
                    SET phone_number = ?
                    WHERE id = ?
                """, (decrypted_phone, row['id']))
            print(f"    Decrypted {len(rows)} account activity log records")
            
            conn.commit()
        
        print("\n✓ Database decryption completed successfully!")
        print(f"  Decrypted database saved to: {output_db}")
        return True
        
    except Exception as e:
        print(f"\n✗ Error decrypting database: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


def load_device_info_from_json(json_file: str) -> tuple:
    """
    Load device information from JSON file.
    
    Args:
        json_file: Path to JSON file with device info
        
    Returns:
        Tuple of (hostname, machine, system)
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        hostname = data.get('hostname', '')
        machine = data.get('machine', '')
        system = data.get('system', '')
        
        if not all([hostname, machine, system]):
            raise ValueError("JSON file must contain 'hostname', 'machine', and 'system' fields")
        
        return hostname, machine, system
    except FileNotFoundError:
        raise FileNotFoundError(f"Device info file not found: {json_file}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Decrypt encrypted database for support purposes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # With device info as arguments:
  python scripts/decrypt_database_for_support.py input.db output_decrypted.db --hostname "DESKTOP-ABC" --machine "AMD64" --system "Windows"
  
  # With device info from JSON file:
  python scripts/decrypt_database_for_support.py input.db output_decrypted.db --device-info device_info.json
  
  # Interactive mode (will prompt for device info):
  python scripts/decrypt_database_for_support.py input.db output_decrypted.db

Device Info JSON format:
  {
    "hostname": "DESKTOP-ABC",
    "machine": "AMD64",
    "system": "Windows"
  }
        """
    )
    
    parser.add_argument(
        'input_db',
        help='Path to encrypted database file'
    )
    
    parser.add_argument(
        'output_db',
        help='Path to output decrypted database file'
    )
    
    parser.add_argument(
        '--hostname',
        help='Device hostname (platform.node())'
    )
    
    parser.add_argument(
        '--machine',
        help='Machine type (platform.machine())'
    )
    
    parser.add_argument(
        '--system',
        help='Operating system (platform.system())'
    )
    
    parser.add_argument(
        '--device-info',
        dest='device_info_file',
        help='Path to JSON file containing device info (hostname, machine, system)'
    )
    
    args = parser.parse_args()
    
    # Validate input database exists
    if not Path(args.input_db).exists():
        print(f"Error: Input database not found: {args.input_db}", file=sys.stderr)
        sys.exit(1)
    
    # Get device information
    hostname = None
    machine = None
    system = None
    
    if args.device_info_file:
        try:
            hostname, machine, system = load_device_info_from_json(args.device_info_file)
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.hostname and args.machine and args.system:
        hostname = args.hostname
        machine = args.machine
        system = args.system
    else:
        # Interactive mode
        print("Database Decryption Script for Support")
        print("=" * 50)
        print("\nPlease provide device information:")
        print("(This can be found in Settings → Security tab)\n")
        
        try:
            hostname = input("Hostname (platform.node()): ").strip()
            machine = input("Machine type (platform.machine()): ").strip()
            system = input("Operating system (platform.system()): ").strip()
            
            if not all([hostname, machine, system]):
                print("Error: All device information fields are required", file=sys.stderr)
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n\nCancelled by user.")
            sys.exit(1)
    
    # Decrypt database
    print("\nStarting database decryption...")
    print(f"Input database: {args.input_db}")
    print(f"Output database: {args.output_db}")
    print(f"Device: {hostname} ({machine}, {system})")
    print("-" * 50)
    
    success = decrypt_database(args.input_db, args.output_db, hostname, machine, system)
    
    if not success:
        print("\n✗ Database decryption failed. Please check the error messages above.", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

