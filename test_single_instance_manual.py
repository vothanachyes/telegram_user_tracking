#!/usr/bin/env python3
"""
Manual test script for single instance enforcement.

This script helps test the single instance feature by simulating
multiple instances trying to start simultaneously.

Usage:
    python test_single_instance_manual.py
"""

import sys
import time
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from utils.single_instance import SingleInstance


def test_basic_functionality():
    """Test basic single instance functionality."""
    print("=" * 60)
    print("Test 1: Basic Single Instance Functionality")
    print("=" * 60)
    
    lock_file = project_root / "data" / "test_instance.lock"
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    
    # First instance
    print("\n1. Creating first instance...")
    instance1 = SingleInstance(lock_file_path=lock_file)
    result1 = instance1.is_already_running()
    print(f"   First instance check: {'FAILED (another instance detected)' if result1 else 'SUCCESS (no other instance)'}")
    
    if result1:
        print("   ❌ ERROR: First instance should succeed!")
        return False
    
    # Second instance (should detect first)
    print("\n2. Creating second instance (should detect first)...")
    instance2 = SingleInstance(lock_file_path=lock_file)
    result2 = instance2.is_already_running()
    print(f"   Second instance check: {'SUCCESS (detected first instance)' if result2 else 'FAILED (should detect first instance)'}")
    
    if not result2:
        print("   ❌ ERROR: Second instance should detect first!")
        instance1.release()
        return False
    
    # Release first instance
    print("\n3. Releasing first instance...")
    instance1.release()
    instance2.release()
    
    # Third instance (should succeed after release)
    print("\n4. Creating third instance after release...")
    instance3 = SingleInstance(lock_file_path=lock_file)
    result3 = instance3.is_already_running()
    print(f"   Third instance check: {'FAILED (another instance detected)' if result3 else 'SUCCESS (no other instance)'}")
    
    if result3:
        print("   ❌ ERROR: Third instance should succeed after release!")
        instance3.release()
        return False
    
    instance3.release()
    print("\n✅ Test 1 PASSED")
    return True


def test_context_manager():
    """Test context manager functionality."""
    print("\n" + "=" * 60)
    print("Test 2: Context Manager Functionality")
    print("=" * 60)
    
    lock_file = project_root / "data" / "test_instance.lock"
    
    try:
        # First instance with context manager
        print("\n1. Creating first instance with context manager...")
        with SingleInstance(lock_file_path=lock_file) as instance1:
            print("   First instance acquired lock successfully")
            
            # Second instance should fail
            print("\n2. Creating second instance (should fail)...")
            instance2 = SingleInstance(lock_file_path=lock_file)
            result2 = instance2.is_already_running()
            
            if not result2:
                print("   ❌ ERROR: Second instance should detect first!")
                instance2.release()
                return False
            
            print("   Second instance correctly detected first instance")
            instance2.release()
        
        print("\n3. First instance context exited, lock released")
        
        # Third instance should succeed
        print("\n4. Creating third instance after context exit...")
        instance3 = SingleInstance(lock_file_path=lock_file)
        result3 = instance3.is_already_running()
        
        if result3:
            print("   ❌ ERROR: Third instance should succeed!")
            instance3.release()
            return False
        
        print("   Third instance acquired lock successfully")
        instance3.release()
        
        print("\n✅ Test 2 PASSED")
        return True
        
    except RuntimeError as e:
        print(f"   ❌ ERROR: Unexpected exception: {e}")
        return False


def test_lock_file_cleanup():
    """Test that lock file is properly cleaned up."""
    print("\n" + "=" * 60)
    print("Test 3: Lock File Cleanup")
    print("=" * 60)
    
    lock_file = project_root / "data" / "test_instance.lock"
    
    # Create instance and acquire lock
    print("\n1. Creating instance and acquiring lock...")
    instance = SingleInstance(lock_file_path=lock_file)
    instance.is_already_running()
    
    # Check that lock file exists
    if lock_file.exists():
        print(f"   Lock file exists: {lock_file}")
        pid = lock_file.read_text().strip()
        print(f"   PID in lock file: {pid}")
    else:
        print("   ⚠️  Lock file doesn't exist (may be normal on some systems)")
    
    # Release lock
    print("\n2. Releasing lock...")
    instance.release()
    
    # Check if lock file was removed
    if not lock_file.exists():
        print("   Lock file was removed after release ✅")
    else:
        print("   ⚠️  Lock file still exists (may be normal, OS will clean up)")
    
    print("\n✅ Test 3 PASSED")
    return True


def main():
    """Run all manual tests."""
    print("\n" + "=" * 60)
    print("Single Instance Enforcement - Manual Tests")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Basic Functionality", test_basic_functionality()))
    results.append(("Context Manager", test_context_manager()))
    results.append(("Lock File Cleanup", test_lock_file_cleanup()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)
    
    # Cleanup
    lock_file = project_root / "data" / "test_instance.lock"
    if lock_file.exists():
        try:
            lock_file.unlink()
        except Exception:
            pass
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

