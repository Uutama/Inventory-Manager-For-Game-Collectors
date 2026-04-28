import subprocess
import sys


def install_requirements() -> None:
    print("Installing required dependencies from requirements.txt...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


try:
    from inventory_scraper.im4gcCLI import InventoryManager
except ImportError as exc:
    print("Error: Missing dependencies for the inventory scraper.")
    print(f"Details: {exc}")
    try:
        install_requirements()
        from inventory_scraper.im4gcCLI import InventoryManager
    except subprocess.CalledProcessError:
        print("Automatic install failed. Please run:")
        print("  python -m pip install -r requirements.txt")
        sys.exit(1)


def main() -> None:
    manager = InventoryManager()
    manager.run()


if __name__ == "__main__":
    main()
