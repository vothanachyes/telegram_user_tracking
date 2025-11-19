import os
import sys
import subprocess
from PIL import Image

WINDOWS_SIZES = [16, 32, 48, 64, 128, 256]
MAC_SIZES = [16, 32, 64, 128, 256, 512, 1024]
LINUX_SIZE = 512  # Single PNG only

def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)

def make_windows_icon(src_img: Image.Image, out_dir: str):
    ensure_dir(out_dir)
    sizes = [(s, s) for s in WINDOWS_SIZES]
    ico_path = os.path.join(out_dir, "icon.ico")
    src_img.save(ico_path, format="ICO", sizes=sizes)
    print(f"✅ Windows ICO created at {ico_path}")

def make_mac_icns(src_img: Image.Image, out_dir: str):
    ensure_dir(out_dir)
    iconset_dir = os.path.join(out_dir, "icon.iconset")
    ensure_dir(iconset_dir)

    # Save all required sizes
    for size in MAC_SIZES:
        filename = f"icon_{size}x{size}.png"
        resized = src_img.resize((size, size), Image.LANCZOS)
        resized.save(os.path.join(iconset_dir, filename), format="PNG")

    # Run Apple iconutil
    icns_path = os.path.join(out_dir, "icon.icns")
    subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", icns_path], check=True)

    # Cleanup
    subprocess.run(["rm", "-rf", iconset_dir])
    print(f"✅ macOS ICNS created at {icns_path}")

def make_linux_png(src_img: Image.Image, out_dir: str):
    ensure_dir(out_dir)
    out_path = os.path.join(out_dir, "icon.png")
    resized = src_img.resize((LINUX_SIZE, LINUX_SIZE), Image.LANCZOS)
    resized.save(out_path, format="PNG")
    print(f"✅ Linux PNG created at {out_path}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Look for icon in parent directory (project root)
    project_root = os.path.dirname(script_dir)
    default_icon = os.path.join(project_root, "assets/appLogo.png")

    input_path = sys.argv[1] if len(sys.argv) >= 2 else default_icon
    print(f"Using input image: {input_path}")

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found")
        sys.exit(1)

    base_img = Image.open(input_path).convert("RGBA")

    # Output icons to project root/icons/ directory
    icons_dir = os.path.join(project_root, "assets/icons")
    make_windows_icon(base_img, os.path.join(icons_dir, "win"))
    make_mac_icns(base_img, os.path.join(icons_dir, "mac"))
    make_linux_png(base_img, os.path.join(icons_dir, "linux"))

    print("\n🎉 All icons generated in .assets/icons/")


if __name__ == "__main__":
    main()

