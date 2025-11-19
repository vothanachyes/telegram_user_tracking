#!/usr/bin/env python3
"""
PIN Decryption Script for Telegram User Tracking

This script decrypts a PIN using the device information, user ID, and encrypted PIN
exported from the Security tab in Settings.

The PIN is double-encrypted:
1. First encrypted with device key (hostname, machine, system)
2. Then encrypted with Firebase user ID

Usage:
    python scripts/decrypt_pin.py <json_file>
    python scripts/decrypt_pin.py --json '{"hostname": "...", "machine": "...", "system": "...", "user_id": "...", "encrypted_pin": "..."}'
    python scripts/decrypt_pin.py  # Interactive mode - paste JSON when prompted

Requirements:
    pip install cryptography
"""

import json
import sys
import hashlib
import base64
import argparse
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def derive_encryption_key(hostname: str, machine: str, system: str) -> bytes:
    """
    Derive encryption key from device-specific information.
    
    This replicates the exact key derivation process used in CredentialStorage.
    
    Args:
        hostname: Device hostname (platform.node())
        machine: Machine type (platform.machine())
        system: Operating system (platform.system())
        
    Returns:
        Base64-encoded Fernet key
    """
    # Replicate the machine_info format
    machine_info = f"{hostname}-{machine}-{system}"
    
    # Generate salt (first 16 bytes of SHA256 hash)
    salt = hashlib.sha256(machine_info.encode()).digest()[:16]
    
    # Generate password (SHA256 hash digest)
    password = hashlib.sha256(machine_info.encode()).digest()
    
    # Derive key using PBKDF2HMAC
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    # Derive and encode key
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key


def derive_user_encryption_key(user_id: str) -> bytes:
    """
    Derive encryption key from Firebase user ID.
    
    This replicates the exact key derivation process used in encrypt_pin_with_user_id.
    
    Args:
        user_id: Firebase user ID (UID)
        
    Returns:
        Base64-encoded Fernet key
    """
    # Derive encryption key from user ID (same as encryption)
    salt = hashlib.sha256(f"user-pin-encryption-{user_id}".encode()).digest()[:16]
    password = hashlib.sha256(f"{user_id}-pin-encryption".encode()).digest()
    
    # Derive key using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key


def decrypt_pin(user_encrypted_pin: str, user_id: str, hostname: str, machine: str, system: str) -> str:
    """
    Decrypt PIN using user ID and device information (double decryption).
    
    The PIN is encrypted twice:
    1. First with device key (hostname, machine, system)
    2. Then with Firebase user ID
    
    Args:
        user_encrypted_pin: Base64-encoded PIN encrypted with user ID
        user_id: Firebase user ID (UID)
        hostname: Device hostname
        machine: Machine type
        system: Operating system
        
    Returns:
        Decrypted PIN (6 digits)
        
    Raises:
        ValueError: If decryption fails
    """
    try:
        # Step 1: Decrypt with user ID key
        user_key = derive_user_encryption_key(user_id)
        user_cipher = Fernet(user_key)
        
        # Decode and decrypt first layer (user ID encryption)
        encrypted_bytes = base64.urlsafe_b64decode(user_encrypted_pin.encode())
        device_encrypted_pin = user_cipher.decrypt(encrypted_bytes).decode()
        
        # Step 2: Decrypt with device key
        device_key = derive_encryption_key(hostname, machine, system)
        device_cipher = Fernet(device_key)
        
        # Decode and decrypt second layer (device encryption)
        device_encrypted_bytes = base64.urlsafe_b64decode(device_encrypted_pin.encode())
        decrypted = device_cipher.decrypt(device_encrypted_bytes)
        
        # Return as string
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt PIN: {e}")


def load_json_from_file(file_path: str) -> dict:
    """Load JSON from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file: {e}")


def load_json_from_string(json_str: str) -> dict:
    """Load JSON from string."""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON string: {e}")


def validate_json_data(data: dict) -> tuple:
    """Validate and extract required fields from JSON."""
    required_fields = ['hostname', 'machine', 'system', 'user_id', 'encrypted_pin']
    
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    hostname = str(data['hostname'])
    machine = str(data['machine'])
    system = str(data['system'])
    user_id = str(data['user_id'])
    encrypted_pin = str(data['encrypted_pin'])
    
    if not encrypted_pin:
        raise ValueError("encrypted_pin cannot be empty")
    
    if not user_id:
        raise ValueError("user_id cannot be empty")
    
    return hostname, machine, system, user_id, encrypted_pin


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Decrypt PIN from exported recovery data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From file:
  python scripts/decrypt_pin.py recovery_data.json
  
  # From JSON string:
  python scripts/decrypt_pin.py --json '{"hostname": "...", "machine": "...", "system": "...", "user_id": "...", "encrypted_pin": "..."}'
  
  # Interactive mode:
  python scripts/decrypt_pin.py
        """
    )
    
    parser.add_argument(
        'json_file',
        nargs='?',
        help='Path to JSON file containing recovery data'
    )
    
    parser.add_argument(
        '--json',
        dest='json_string',
        help='JSON string containing recovery data'
    )
    
    args = parser.parse_args()
    
    # Load JSON data
    try:
        if args.json_string:
            data = load_json_from_string(args.json_string)
        elif args.json_file:
            data = load_json_from_file(args.json_file)
        else:
            # Interactive mode
            print("PIN Decryption Script")
            print("=" * 50)
            print("\nPaste the JSON data from the Security tab (or press Ctrl+D/Ctrl+Z to exit):\n")
            try:
                json_lines = []
                while True:
                    try:
                        line = input()
                        json_lines.append(line)
                    except EOFError:
                        break
                json_str = '\n'.join(json_lines)
                if not json_str.strip():
                    print("No input provided. Exiting.")
                    sys.exit(1)
                data = load_json_from_string(json_str)
            except KeyboardInterrupt:
                print("\n\nCancelled by user.")
                sys.exit(1)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Validate and extract data
    try:
        hostname, machine, system, user_id, encrypted_pin = validate_json_data(data)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Decrypt PIN
    try:
        print("\nDecrypting PIN...")
        print(f"Device: {hostname} ({machine}, {system})")
        print(f"User ID: {user_id[:8]}...")  # Show first 8 chars for privacy
        print("-" * 50)
        
        pin = decrypt_pin(encrypted_pin, user_id, hostname, machine, system)
        
        print(f"\n✓ PIN Decrypted Successfully!")
        print(f"\nYour PIN is: {pin}\n")
        
    except ValueError as e:
        print(f"\n✗ Decryption failed: {e}", file=sys.stderr)
        print("\nPossible reasons:")
        print("  - Device information doesn't match the original device")
        print("  - User ID doesn't match the original user")
        print("  - Encrypted PIN is corrupted or invalid")
        print("  - JSON data is incorrect")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

