"""
Automated update deployment script.
Handles building, checksum calculation, GitHub release, and Firebase update.
"""

import os
import sys
import hashlib
import platform
import subprocess
import argparse
import time
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Tuple

# Load environment variables from .env.deploy (preferred) or .env (fallback)
try:
    from dotenv import load_dotenv
    # Try .env.deploy first (deployment-specific), then .env (development)
    deploy_env = Path(__file__).resolve().parent.parent / '.env.deploy'
    dev_env = Path(__file__).resolve().parent.parent / '.env'
    
    if deploy_env.exists():
        load_dotenv(deploy_env)
        print(f"📋 Loaded environment from: .env.deploy")
    elif dev_env.exists():
        load_dotenv(dev_env)
        print(f"📋 Loaded environment from: .env (consider using .env.deploy for deployment)")
    else:
        print("⚠️  No .env.deploy or .env file found - using system environment variables")
except ImportError:
    # python-dotenv not installed, use system environment variables
    pass

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  requests library not installed. Install with: pip install requests")

try:
    from firebase_admin import credentials, firestore
    import firebase_admin
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️  Firebase Admin SDK not installed. Install with: pip install firebase-admin")

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def detect_platform_strategy() -> Tuple[str, list]:
    """
    Detect current platform and determine build strategy.
    
    Returns:
        Tuple of (strategy, platforms_to_build)
        strategy: "mac" or "windows"
        platforms_to_build: List of platforms to build
    """
    current_platform = platform.system()
    
    if current_platform == "Darwin":  # macOS
        return ("mac", ["macos", "linux"])
    elif current_platform == "Windows":
        return ("windows", ["windows"])
    else:  # Linux
        return ("linux", ["linux"])


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    return file_path.stat().st_size


def build_app(platform_name: Optional[str] = None) -> Dict[str, Path]:
    """
    Build app for specified platform(s).
    
    Args:
        platform_name: 'windows', 'macos', 'linux', or None for current platform
    
    Returns:
        Dict mapping platform to executable path
    """
    builds = {}
    current_platform = platform.system()
    
    platforms_to_build = []
    if platform_name:
        platforms_to_build = [platform_name.lower()]
    else:
        # Build for current platform only
        if current_platform == "Windows":
            platforms_to_build = ["windows"]
        elif current_platform == "Darwin":
            platforms_to_build = ["macos"]
        else:
            platforms_to_build = ["linux"]
    
    print(f"\n{'='*60}")
    print("Building Application")
    print(f"{'='*60}")
    
    for platform_name in platforms_to_build:
        print(f"\n📦 Building for {platform_name}...")
        
        # Run build script
        build_script = PROJECT_ROOT / "scripts" / "build.py"
        result = subprocess.run(
            [sys.executable, str(build_script)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Build failed for {platform_name}")
            print(result.stderr)
            continue
        
        # Find built executable
        dist_dir = PROJECT_ROOT / "dist"
        if platform_name == "windows":
            exe_path = dist_dir / "TelegramUserTracking.exe"
        elif platform_name == "macos":
            exe_path = dist_dir / "TelegramUserTracking"
        else:  # linux
            exe_path = dist_dir / "TelegramUserTracking"
        
        if exe_path.exists():
            builds[platform_name] = exe_path
            size_mb = get_file_size(exe_path) / (1024 * 1024)
            print(f"✅ Built: {exe_path} ({size_mb:.2f} MB)")
        else:
            print(f"⚠️  Executable not found at {exe_path}")
    
    return builds


def create_and_push_tag(version: str) -> bool:
    """
    Create git tag and push to remote repository.
    
    Args:
        version: Version string (e.g., "1.0.1")
    
    Returns:
        True if successful, False otherwise
    """
    tag_name = f"v{version}"
    
    print(f"\n{'='*60}")
    print("Creating Git Tag")
    print(f"{'='*60}")
    print(f"Tag: {tag_name}")
    
    try:
        # Check if tag already exists
        result = subprocess.run(
            ["git", "tag", "-l", tag_name],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        if tag_name in result.stdout:
            print(f"⚠️  Tag {tag_name} already exists")
            response = input(f"Delete and recreate tag {tag_name}? (y/N): ")
            if response.lower() == 'y':
                subprocess.run(
                    ["git", "tag", "-d", tag_name],
                    cwd=PROJECT_ROOT,
                    check=True
                )
                subprocess.run(
                    ["git", "push", "origin", "--delete", tag_name],
                    cwd=PROJECT_ROOT,
                    capture_output=True
                )
            else:
                print(f"Using existing tag {tag_name}")
                return True
        
        # Create tag
        subprocess.run(
            ["git", "tag", tag_name],
            cwd=PROJECT_ROOT,
            check=True
        )
        print(f"✅ Tag created: {tag_name}")
        
        # Push tag
        subprocess.run(
            ["git", "push", "origin", tag_name],
            cwd=PROJECT_ROOT,
            check=True
        )
        print(f"✅ Tag pushed: {tag_name}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create/push tag: {e}")
        return False
    except FileNotFoundError:
        print("❌ Git not found. Make sure git is installed and in PATH")
        return False


def trigger_github_workflow(
    github_token: str,
    repo_owner: str,
    repo_name: str,
    workflow_name: str,
    version: str
) -> Optional[int]:
    """
    Trigger GitHub Actions workflow via API.
    
    Args:
        github_token: GitHub personal access token
        repo_owner: Repository owner
        repo_name: Repository name
        workflow_name: Workflow name or file
        version: Version string (for workflow_dispatch inputs)
    
    Returns:
        Workflow run ID or None if failed
    """
    if not REQUESTS_AVAILABLE:
        print("❌ requests library not available")
        return None
    
    print(f"\n{'='*60}")
    print("Triggering GitHub Actions Workflow")
    print(f"{'='*60}")
    
    # Get workflow ID by name
    workflows_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        # List workflows to find the one we want
        response = requests.get(workflows_url, headers=headers, timeout=30)
        response.raise_for_status()
        workflows = response.json().get("workflows", [])
        
        workflow_id = None
        for workflow in workflows:
            if workflow["name"] == workflow_name or workflow["path"].endswith(workflow_name):
                workflow_id = workflow["id"]
                break
        
        if not workflow_id:
            print(f"⚠️  Workflow '{workflow_name}' not found")
            print("   Available workflows:")
            for wf in workflows:
                print(f"     - {wf['name']} ({wf['path']})")
            return None
        
        # Trigger workflow
        dispatch_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/{workflow_id}/dispatches"
        dispatch_data = {
            "ref": "main",  # or "master"
            "inputs": {
                "version": version
            }
        }
        
        response = requests.post(dispatch_url, json=dispatch_data, headers=headers, timeout=30)
        
        if response.status_code == 204:
            print(f"✅ Workflow triggered: {workflow_name}")
            # Wait a moment for workflow to start, then get run ID
            time.sleep(2)
            return get_latest_workflow_run_id(github_token, repo_owner, repo_name, workflow_id)
        else:
            print(f"❌ Failed to trigger workflow: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error triggering workflow: {e}")
        return None


def get_latest_workflow_run_id(
    github_token: str,
    repo_owner: str,
    repo_name: str,
    workflow_id: int
) -> Optional[int]:
    """Get the latest workflow run ID."""
    runs_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/{workflow_id}/runs"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(runs_url, headers=headers, params={"per_page": 1}, timeout=30)
        response.raise_for_status()
        runs = response.json().get("workflow_runs", [])
        if runs:
            return runs[0]["id"]
        return None
    except requests.exceptions.RequestException:
        return None


def wait_for_workflow_completion(
    github_token: str,
    repo_owner: str,
    repo_name: str,
    run_id: int,
    timeout: int = 1800  # 30 minutes
) -> bool:
    """
    Wait for GitHub Actions workflow to complete.
    
    Args:
        github_token: GitHub personal access token
        repo_owner: Repository owner
        repo_name: Repository name
        run_id: Workflow run ID
        timeout: Maximum time to wait in seconds
    
    Returns:
        True if successful, False if failed or timeout
    """
    if not REQUESTS_AVAILABLE:
        print("❌ requests library not available")
        return False
    
    print(f"\n{'='*60}")
    print("Waiting for Workflow Completion")
    print(f"{'='*60}")
    print(f"Run ID: {run_id}")
    print("This may take several minutes...")
    
    run_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs/{run_id}"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(run_url, headers=headers, timeout=30)
            response.raise_for_status()
            run_info = response.json()
            
            status = run_info.get("status")
            conclusion = run_info.get("conclusion")
            
            if status != last_status:
                print(f"  Status: {status}")
                last_status = status
            
            if status == "completed":
                if conclusion == "success":
                    print(f"✅ Workflow completed successfully!")
                    return True
                else:
                    print(f"❌ Workflow failed with conclusion: {conclusion}")
                    return False
            
            time.sleep(10)  # Poll every 10 seconds
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Error checking workflow status: {e}")
            time.sleep(10)
    
    print(f"❌ Workflow timeout after {timeout} seconds")
    return False


def download_artifact(
    github_token: str,
    repo_owner: str,
    repo_name: str,
    run_id: int,
    artifact_name: str,
    output_path: Path
) -> bool:
    """
    Download artifact from GitHub Actions workflow run.
    
    Args:
        github_token: GitHub personal access token
        repo_owner: Repository owner
        repo_name: Repository name
        run_id: Workflow run ID
        artifact_name: Name of the artifact to download
        output_path: Path to save the artifact
    
    Returns:
        True if successful, False otherwise
    """
    if not REQUESTS_AVAILABLE:
        print("❌ requests library not available")
        return False
    
    print(f"\n{'='*60}")
    print("Downloading Artifact")
    print(f"{'='*60}")
    print(f"Artifact: {artifact_name}")
    print(f"Output: {output_path}")
    
    artifacts_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs/{run_id}/artifacts"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        # List artifacts
        response = requests.get(artifacts_url, headers=headers, timeout=30)
        response.raise_for_status()
        artifacts = response.json().get("artifacts", [])
        
        artifact = None
        for art in artifacts:
            if art["name"] == artifact_name:
                artifact = art
                break
        
        if not artifact:
            print(f"❌ Artifact '{artifact_name}' not found")
            print("   Available artifacts:")
            for art in artifacts:
                print(f"     - {art['name']}")
            return False
        
        # Download artifact
        download_url = artifact["archive_download_url"]
        response = requests.get(download_url, headers=headers, stream=True, timeout=300)
        response.raise_for_status()
        
        # Save as zip
        zip_path = output_path.parent / f"{artifact_name}.zip"
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Artifact downloaded: {zip_path}")
        
        # Extract zip
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_path.parent)
        
        # Find the actual executable in extracted files
        extracted_dir = output_path.parent
        for file in extracted_dir.rglob("TelegramUserTracking.exe"):
            # Move to dist/ if not already there
            if file.parent != output_path.parent:
                file.rename(output_path)
            else:
                output_path = file
            break
        
        # Clean up zip
        zip_path.unlink()
        
        if output_path.exists():
            size_mb = get_file_size(output_path) / (1024 * 1024)
            print(f"✅ Artifact extracted: {output_path} ({size_mb:.2f} MB)")
            return True
        else:
            print(f"⚠️  Executable not found in extracted artifact")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading artifact: {e}")
        return False
    except zipfile.BadZipFile:
        print(f"❌ Invalid zip file")
        return False


def find_existing_binaries() -> Dict[str, Path]:
    """
    Find existing binaries in dist/ directory.
    
    Returns:
        Dict mapping platform to file path
    """
    binaries = {}
    dist_dir = PROJECT_ROOT / "dist"
    
    if not dist_dir.exists():
        return binaries
    
    # Check for Windows
    windows_exe = dist_dir / "TelegramUserTracking.exe"
    if windows_exe.exists():
        binaries["windows"] = windows_exe
    
    # Check for Mac/Linux (same name, need to detect)
    mac_linux_exe = dist_dir / "TelegramUserTracking"
    if mac_linux_exe.exists():
        # Try to detect platform from file
        # On Mac, we'll assume it's Mac binary if we're on Mac
        # On Linux, we'll assume it's Linux binary if we're on Linux
        current_system = platform.system()
        if current_system == "Darwin":
            binaries["macos"] = mac_linux_exe
        elif current_system == "Linux":
            binaries["linux"] = mac_linux_exe
        else:
            # Unknown, try both
            binaries["macos"] = mac_linux_exe
            binaries["linux"] = mac_linux_exe
    
    return binaries


def create_github_release(
    version: str,
    release_notes: str,
    github_token: str,
    repo_owner: str,
    repo_name: str,
    binaries: Dict[str, Path]
) -> Optional[str]:
    """
    Create GitHub release and upload binaries.
    
    Args:
        version: Version string (e.g., "1.0.1")
        release_notes: Release notes
        github_token: GitHub personal access token
        repo_owner: Repository owner
        repo_name: Repository name
        binaries: Dict mapping platform to file path
    
    Returns:
        Release URL or None if failed
    """
    if not REQUESTS_AVAILABLE:
        print("❌ requests library not available")
        return None
    
    print(f"\n{'='*60}")
    print("Creating GitHub Release")
    print(f"{'='*60}")
    
    # Create release
    release_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    release_data = {
        "tag_name": f"v{version}",
        "name": f"Version {version}",
        "body": release_notes,
        "draft": False,
        "prerelease": False
    }
    
    print(f"Creating release v{version}...")
    try:
        response = requests.post(release_url, json=release_data, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to create release: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None
    
    release_info = response.json()
    release_id = release_info["id"]
    upload_url = release_info["upload_url"].split("{")[0]
    html_url = release_info["html_url"]
    
    print(f"✅ Release created: {html_url}")
    
    # Upload binaries
    print(f"\n📤 Uploading binaries...")
    uploaded_count = 0
    for platform_name, file_path in binaries.items():
        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            continue
        
        # Determine filename
        ext = ".exe" if platform_name == "windows" else (".dmg" if platform_name == "macos" else "")
        filename = f"TelegramUserTracking-v{version}-{platform_name}{ext}"
        
        print(f"  Uploading {filename}...")
        
        try:
            with open(file_path, 'rb') as f:
                upload_headers = {
                    **headers,
                    "Content-Type": "application/octet-stream"
                }
                upload_response = requests.post(
                    f"{upload_url}?name={filename}",
                    headers=upload_headers,
                    data=f,
                    timeout=300  # 5 minutes for large files
                )
                upload_response.raise_for_status()
                print(f"  ✅ Uploaded: {filename}")
                uploaded_count += 1
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Failed to upload {filename}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Response: {e.response.text}")
    
    if uploaded_count == 0:
        print("⚠️  No binaries were uploaded")
        return None
    
    print(f"\n✅ Uploaded {uploaded_count} binary(ies)")
    return html_url


def update_firebase(
    version: str,
    binaries: Dict[str, Path],
    release_url: str,
    release_notes: str = "",
    min_version_required: Optional[str] = None
) -> bool:
    """
    Update Firebase Firestore with new version info.
    
    Args:
        version: Version string
        binaries: Dict mapping platform to file path
        release_url: GitHub release URL
        release_notes: Release notes
        min_version_required: Minimum version required to update
    
    Returns:
        True if successful
    """
    if not FIREBASE_AVAILABLE:
        print("❌ Firebase Admin SDK not available")
        return False
    
    print(f"\n{'='*60}")
    print("Updating Firebase")
    print(f"{'='*60}")
    
    try:
        # Initialize Firebase if not already initialized
        if not firebase_admin._apps:
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
            if not cred_path or not Path(cred_path).exists():
                print("❌ Firebase credentials not found")
                print("   Set FIREBASE_CREDENTIALS_PATH environment variable")
                return False
            
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized")
        
        db = firestore.client()
        
        # Prepare update data
        update_data = {
            "version": version,
            "release_date": datetime.utcnow().isoformat() + "Z",
            "is_available": True,
            "release_notes": release_notes
        }
        
        if min_version_required:
            update_data["min_version_required"] = min_version_required
        
        # Add platform-specific data
        for platform_name, file_path in binaries.items():
            if not file_path.exists():
                continue
            
            checksum = calculate_sha256(file_path)
            file_size = get_file_size(file_path)
            
            # Get download URL from GitHub release
            # Format: https://github.com/OWNER/REPO/releases/download/vVERSION/filename
            ext = ".exe" if platform_name == "windows" else (".dmg" if platform_name == "macos" else "")
            filename = f"TelegramUserTracking-v{version}-{platform_name}{ext}"
            
            # Extract repo info from release_url
            # release_url format: https://github.com/OWNER/REPO/releases/tag/vVERSION
            # Convert to download URL
            download_url = release_url.replace("releases/tag/", "releases/download/") + f"/{filename}"
            
            if platform_name == "windows":
                update_data["download_url_windows"] = download_url
                update_data["checksum_windows"] = checksum
                update_data["file_size_windows"] = file_size
            elif platform_name == "macos":
                update_data["download_url_macos"] = download_url
                update_data["checksum_macos"] = checksum
                update_data["file_size_macos"] = file_size
            else:  # linux
                update_data["download_url_linux"] = download_url
                update_data["checksum_linux"] = checksum
                update_data["file_size_linux"] = file_size
            
            size_mb = file_size / (1024 * 1024)
            print(f"  ✅ {platform_name}: checksum={checksum[:16]}..., size={size_mb:.2f} MB")
        
        # Update Firestore
        from utils.constants import FIREBASE_APP_UPDATES_COLLECTION, FIREBASE_APP_UPDATES_DOCUMENT
        
        doc_ref = db.collection(FIREBASE_APP_UPDATES_COLLECTION).document(FIREBASE_APP_UPDATES_DOCUMENT)
        doc_ref.set(update_data, merge=True)
        
        print(f"\n✅ Firebase updated with version {version}")
        print(f"   Document: {FIREBASE_APP_UPDATES_COLLECTION}/{FIREBASE_APP_UPDATES_DOCUMENT}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating Firebase: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(
        description="Deploy app update to GitHub releases and Firebase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # One-command deployment (auto-detects platform)
  python scripts/deploy_update.py 1.0.1 --release-notes "Bug fixes"
  
  # Deploy with pre-built binaries (skip build)
  python scripts/deploy_update.py 1.0.1 --skip-build
  
  # Build only (no deployment)
  python scripts/deploy_update.py 1.0.1 --skip-github --skip-firebase
  
Environment Variables:
  GITHUB_TOKEN - GitHub personal access token (required for GitHub)
  GITHUB_REPO_OWNER - Repository owner (required for GitHub)
  GITHUB_REPO_NAME - Repository name (required for GitHub)
  GITHUB_PRIVATE_REPO_OWNER - Private repo owner (for CI/CD, optional)
  GITHUB_PRIVATE_REPO_NAME - Private repo name (for CI/CD, optional)
  GITHUB_WORKFLOW_NAME - Workflow name (default: "Build Windows Executable")
  FIREBASE_CREDENTIALS_PATH - Path to Firebase credentials JSON (required for Firebase)
        """
    )
    parser.add_argument("version", help="Version string (e.g., 1.0.1)")
    parser.add_argument("--platform", choices=["windows", "macos", "linux"], 
                       help="Platform to build (default: auto-detect)")
    parser.add_argument("--release-notes", default="", help="Release notes")
    parser.add_argument("--min-version", help="Minimum version required to update")
    parser.add_argument("--skip-build", action="store_true", help="Skip building (use existing binaries)")
    parser.add_argument("--skip-github", action="store_true", help="Skip GitHub release")
    parser.add_argument("--skip-firebase", action="store_true", help="Skip Firebase update")
    parser.add_argument("--skip-windows-ci", action="store_true", help="Skip Windows CI/CD build (Mac only)")
    parser.add_argument("--github-token", help="GitHub personal access token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--repo-owner", help="GitHub repository owner (or set GITHUB_REPO_OWNER env var)")
    parser.add_argument("--repo-name", help="GitHub repository name (or set GITHUB_REPO_NAME env var)")
    parser.add_argument("--private-repo-owner", help="Private repo owner (or set GITHUB_PRIVATE_REPO_OWNER env var)")
    parser.add_argument("--private-repo-name", help="Private repo name (or set GITHUB_PRIVATE_REPO_NAME env var)")
    parser.add_argument("--workflow-name", help="Workflow name (or set GITHUB_WORKFLOW_NAME env var)")
    
    args = parser.parse_args()
    
    print("="*60)
    print("Automated Update Deployment")
    print("="*60)
    print(f"Version: {args.version}")
    
    # Detect platform strategy
    strategy, platforms_to_build = detect_platform_strategy()
    current_platform = platform.system()
    print(f"Platform: {current_platform} (strategy: {strategy})")
    print("="*60)
    
    # Get GitHub credentials
    github_token = args.github_token or os.getenv("GITHUB_TOKEN")
    private_repo_owner = args.private_repo_owner or os.getenv("GITHUB_PRIVATE_REPO_OWNER", "")
    private_repo_name = args.private_repo_name or os.getenv("GITHUB_PRIVATE_REPO_NAME", "")
    workflow_name = args.workflow_name or os.getenv("GITHUB_WORKFLOW_NAME", "Build Windows Executable")
    
    binaries = {}
    
    # Smart workflow based on platform
    if not args.skip_build:
        if strategy == "mac" and not args.skip_windows_ci:
            # Mac workflow: Trigger Windows CI/CD, then build Mac/Linux locally
            print(f"\n{'='*60}")
            print("Mac Workflow: CI/CD for Windows + Local Build for Mac/Linux")
            print(f"{'='*60}")
            
            # Check if we have private repo info for CI/CD
            if not private_repo_owner or not private_repo_name:
                print("⚠️  Private repo info not provided. Skipping Windows CI/CD.")
                print("   Set GITHUB_PRIVATE_REPO_OWNER and GITHUB_PRIVATE_REPO_NAME")
                print("   Or use --private-repo-owner and --private-repo-name")
                print("   Falling back to local builds only...")
                strategy = "local_only"
            elif not github_token:
                print("⚠️  GitHub token not provided. Skipping Windows CI/CD.")
                print("   Set GITHUB_TOKEN environment variable")
                print("   Falling back to local builds only...")
                strategy = "local_only"
            else:
                # Create and push tag to trigger CI/CD
                if not create_and_push_tag(args.version):
                    print("⚠️  Failed to create/push tag. Continuing with local builds only...")
                    strategy = "local_only"
                else:
                    # Trigger workflow (or wait for tag-triggered workflow)
                    print("\n⏳ Waiting for tag to trigger workflow (or triggering manually)...")
                    time.sleep(3)  # Give GitHub time to process the tag
                    
                    # Get workflow run ID (from tag push)
                    if private_repo_owner and private_repo_name:
                        # Try to find the workflow run triggered by the tag
                        run_id = get_workflow_run_from_tag(
                            github_token,
                            private_repo_owner,
                            private_repo_name,
                            f"v{args.version}"
                        )
                        
                        if run_id:
                            print(f"✅ Found workflow run: {run_id}")
                            # Wait for completion
                            if wait_for_workflow_completion(
                                github_token,
                                private_repo_owner,
                                private_repo_name,
                                run_id
                            ):
                                # Download Windows artifact
                                dist_dir = PROJECT_ROOT / "dist"
                                dist_dir.mkdir(exist_ok=True)
                                windows_exe = dist_dir / "TelegramUserTracking.exe"
                                
                                if download_artifact(
                                    github_token,
                                    private_repo_owner,
                                    private_repo_name,
                                    run_id,
                                    "TelegramUserTracking-Windows",
                                    windows_exe
                                ):
                                    binaries["windows"] = windows_exe
                                    print("✅ Windows binary ready from CI/CD")
                                else:
                                    print("⚠️  Failed to download Windows artifact")
                            else:
                                print("⚠️  Windows build failed. Continuing with Mac/Linux only...")
                        else:
                            print("⚠️  Could not find workflow run. Continuing with local builds only...")
        
        # Build local platforms
        if strategy == "local_only" or (strategy == "mac" and platforms_to_build):
            print(f"\n{'='*60}")
            print("Building Local Platforms")
            print(f"{'='*60}")
            for platform_name in platforms_to_build:
                if args.platform and platform_name != args.platform:
                    continue
                local_builds = build_app(platform_name)
                binaries.update(local_builds)
        
        elif strategy == "windows":
            # Windows workflow: Build locally only
            print(f"\n{'='*60}")
            print("Windows Workflow: Local Build Only")
            print(f"{'='*60}")
            local_builds = build_app("windows")
            binaries.update(local_builds)
        
        if not binaries:
            print("❌ No binaries built. Exiting.")
            return 1
    else:
        # Use existing binaries from dist/
        print(f"\n{'='*60}")
        print("Using Existing Binaries")
        print(f"{'='*60}")
        binaries = find_existing_binaries()
        if not binaries:
            print("❌ No binaries found in dist/ directory")
            print("   Build binaries first or remove --skip-build flag")
            return 1
        
        print(f"\nFound {len(binaries)} binary(ies):")
        for platform_name, file_path in binaries.items():
            size_mb = get_file_size(file_path) / (1024 * 1024)
            print(f"  - {platform_name}: {file_path} ({size_mb:.2f} MB)")
    
    # Calculate checksums
    print(f"\n{'='*60}")
    print("Calculating Checksums")
    print(f"{'='*60}")
    checksums = {}
    for platform_name, file_path in binaries.items():
        checksum = calculate_sha256(file_path)
        checksums[platform_name] = checksum
        size_mb = get_file_size(file_path) / (1024 * 1024)
        print(f"{platform_name}: {checksum} ({size_mb:.2f} MB)")
    
    # Create GitHub release
    release_url = None
    if not args.skip_github:
        github_token = args.github_token or os.getenv("GITHUB_TOKEN")
        repo_owner = args.repo_owner or os.getenv("GITHUB_REPO_OWNER", "")
        repo_name = args.repo_name or os.getenv("GITHUB_REPO_NAME", "")
        
        if not github_token:
            print("\n⚠️  GitHub token not provided. Skipping GitHub release.")
            print("   Set GITHUB_TOKEN env var or use --github-token")
        elif not repo_owner or not repo_name:
            print("\n⚠️  Repository info not provided. Skipping GitHub release.")
            print("   Set GITHUB_REPO_OWNER and GITHUB_REPO_NAME env vars")
            print("   Or use --repo-owner and --repo-name")
        else:
            release_url = create_github_release(
                args.version,
                args.release_notes,
                github_token,
                repo_owner,
                repo_name,
                binaries
            )
            if not release_url:
                print("⚠️  GitHub release creation failed")
    
    # Update Firebase
    if not args.skip_firebase:
        if not release_url:
            print("\n⚠️  No release URL available. Using placeholder URLs.")
            # Construct placeholder URL
            repo_owner = args.repo_owner or os.getenv("GITHUB_REPO_OWNER", "your_username")
            repo_name = args.repo_name or os.getenv("GITHUB_REPO_NAME", "telegram_user_tracking-releases")
            release_url = f"https://github.com/{repo_owner}/{repo_name}/releases/tag/v{args.version}"
            print(f"   You'll need to manually update URLs in Firebase after creating release")
        
        success = update_firebase(
            args.version,
            binaries,
            release_url or "",
            args.release_notes,
            args.min_version
        )
        
        if not success:
            print("⚠️  Firebase update failed. You may need to update manually.")
    
    print(f"\n{'='*60}")
    print("✅ Deployment Complete!")
    print(f"{'='*60}")
    if release_url:
        print(f"\nRelease URL: {release_url}")
    print(f"\nNext steps:")
    print(f"1. Verify Firebase document: app_updates/latest")
    if release_url:
        print(f"2. Test download URLs from release page")
    print(f"3. Test update on a user device")
    print(f"4. Monitor update adoption")
    
    return 0


def get_workflow_run_from_tag(
    github_token: str,
    repo_owner: str,
    repo_name: str,
    tag: str
) -> Optional[int]:
    """Get workflow run ID from a tag push."""
    if not REQUESTS_AVAILABLE:
        return None
    
    workflows_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        # Find the workflow
        response = requests.get(workflows_url, headers=headers, timeout=30)
        response.raise_for_status()
        workflows = response.json().get("workflows", [])
        
        workflow_id = None
        for workflow in workflows:
            if "windows" in workflow["name"].lower() or "build" in workflow["name"].lower():
                workflow_id = workflow["id"]
                break
        
        if not workflow_id:
            return None
        
        # Get runs for this workflow
        runs_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/{workflow_id}/runs"
        response = requests.get(
            runs_url,
            headers=headers,
            params={"per_page": 5},
            timeout=30
        )
        response.raise_for_status()
        runs = response.json().get("workflow_runs", [])
        
        # Find run with matching tag
        for run in runs:
            if run.get("head_branch") == tag or tag in run.get("head_branch", ""):
                return run["id"]
        
        # If no exact match, return the latest run (might be the one we just triggered)
        if runs:
            return runs[0]["id"]
        
        return None
    except requests.exceptions.RequestException:
        return None


if __name__ == "__main__":
    sys.exit(main())

