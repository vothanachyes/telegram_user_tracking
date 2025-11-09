"""
Telegram Group Exporter - Main Entry Point

A simple, runnable script to export files and messages from Telegram groups.
"""
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

try:
    from colorama import init, Fore, Style, Back
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    # Fallback colors using ANSI codes
    class Fore:
        RED = '\033[91m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        MAGENTA = '\033[95m'
        CYAN = '\033[96m'
        WHITE = '\033[97m'
        RESET = '\033[0m'
    
    class Style:
        BRIGHT = '\033[1m'
        RESET_ALL = '\033[0m'
    
    class Back:
        BLUE = '\033[44m'
        RESET = '\033[0m'

from config import Config
from exporter import TelegramExporter
from group_info import get_group_info_async


def setup_logging() -> Path:
    """
    Setup logging to save logs by date in logs/ directory.
    
    Returns:
        Path to the log file
    """
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create log file with today's date
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = logs_dir / f"{today}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding='utf-8')
        ],
        force=True  # Override any existing configuration
    )
    
    return log_file


# Setup logging
log_file_path = setup_logging()
logger = logging.getLogger(__name__)
logger.info(f"📝 Logs will be saved to: {log_file_path.absolute()}")


def print_banner() -> None:
    """Print colorful application banner."""
    banner = f"""
{Fore.CYAN}{Style.BRIGHT}   _____ _____ _____ _____ _____ _____ _____ 
{Fore.CYAN}  |_   _|  __ \\_   _/ ____|_   _|  __ \\_   _|
{Fore.CYAN}    | | | |__\\) || || |  __  | | | |__\\) || |  
{Fore.CYAN}    | | |  ___/ | || | |_ | | | |  ___/ | |  
{Fore.CYAN}   _| |_| |    _| || |__| |_| |_| |    _| |_ 
{Fore.CYAN}  |_____|_|   |_____\\_____|_____|_|   |_____|
{Fore.YELLOW}{Style.BRIGHT}  Telegram Group Exporter v3.0
{Style.RESET_ALL}"""
    print(banner)


def print_menu() -> None:
    """Print colorful menu."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*50}")
    print(f"{Fore.CYAN}{Style.BRIGHT}  MAIN MENU")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Style.BRIGHT}  1.{Style.RESET_ALL} {Fore.WHITE}Start fetching{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Style.BRIGHT}  2.{Style.RESET_ALL} {Fore.WHITE}Get group info{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*50}{Style.RESET_ALL}\n")


def print_config() -> None:
    """Print current configuration."""
    print(f"\n{Fore.BLUE}{Style.BRIGHT}⚡ Configuration:{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}-{Style.RESET_ALL} API ID: {Fore.YELLOW}{Config.API_ID}{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}-{Style.RESET_ALL} Phone: {Fore.YELLOW}{Config.PHONE_NUMBER}{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}-{Style.RESET_ALL} Group ID: {Fore.YELLOW}{Config.GROUP_ID}{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}-{Style.RESET_ALL} Export folder: {Fore.YELLOW}{Config.EXPORT_FOLDER}{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}-{Style.RESET_ALL} Max file size: {Fore.YELLOW}{Config.MAX_FILE_SIZE_MB}MB{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}-{Style.RESET_ALL} Rate limit: {Fore.YELLOW}{Config.RATE_LIMIT}s{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}-{Style.RESET_ALL} Max retries: {Fore.YELLOW}{Config.MAX_RETRIES}{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}-{Style.RESET_ALL} Date range: {Fore.YELLOW}{Config.get_start_date().date()} to {Config.get_end_date().date()}{Style.RESET_ALL}")


async def start_fetching() -> None:
    """Start the normal fetching process."""
    print(f"\n{Fore.GREEN}{Style.BRIGHT}🚀 Starting fetch process...{Style.RESET_ALL}\n")
    
    # Validate configuration
    is_valid, error_msg = Config.validate()
    if not is_valid:
        print(f"{Fore.RED}{Style.BRIGHT}❌ Configuration error: {error_msg}{Style.RESET_ALL}")
        return
    
    # Ensure export folder exists
    Config.ensure_export_folder()
    
    print_config()
    
    # Confirm before starting
    try:
        response = input(f"\n{Fore.YELLOW}⚠️  Start export? (yes/no): {Style.RESET_ALL}").strip().lower()
        if response not in ['yes', 'y']:
            print(f"{Fore.YELLOW}Export cancelled by user{Style.RESET_ALL}")
            return
    except (EOFError, KeyboardInterrupt):
        print(f"\n{Fore.YELLOW}Export cancelled{Style.RESET_ALL}")
        return
    
    # Run export
    try:
        async with TelegramExporter(Config) as exporter:
            await exporter.export_history()
            exporter.print_summary()
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}🛑 Export stopped by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}‼️ Fatal error: {str(e)}{Style.RESET_ALL}")
        logger.error(f"Fatal error: {str(e)}", exc_info=True)


async def get_group_info() -> None:
    """Get group information by invite link, username, or ID."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*50}")
    print(f"{Fore.CYAN}{Style.BRIGHT}  GET GROUP INFO")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*50}{Style.RESET_ALL}\n")
    
    print(f"{Fore.YELLOW}Enter group identifier:{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}•{Style.RESET_ALL} Invite link (e.g., https://t.me/joinchat/... or t.me/+...)")
    print(f"  {Fore.CYAN}•{Style.RESET_ALL} Username (e.g., @groupname or groupname)")
    print(f"  {Fore.CYAN}•{Style.RESET_ALL} Group ID (e.g., -1001234567890)\n")
    
    try:
        user_input = input(f"{Fore.GREEN}➜ {Style.RESET_ALL}").strip()
        
        if not user_input:
            print(f"{Fore.RED}❌ No input provided{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.YELLOW}⏳ Fetching group information...{Style.RESET_ALL}\n")
        
        # Validate basic config (API credentials)
        if not Config.API_ID or Config.API_ID == 0:
            print(f"{Fore.RED}❌ API_ID must be set in .env file{Style.RESET_ALL}")
            return
        
        if not Config.API_HASH:
            print(f"{Fore.RED}❌ API_HASH must be set in .env file{Style.RESET_ALL}")
            return
        
        if not Config.PHONE_NUMBER:
            print(f"{Fore.RED}❌ PHONE_NUMBER must be set in .env file{Style.RESET_ALL}")
            return
        
        # Fetch group info
        info = await get_group_info_async(user_input)
        
        if info:
            print(f"\n{Fore.GREEN}{Style.BRIGHT}{'='*50}")
            print(f"{Fore.GREEN}{Style.BRIGHT}  GROUP INFORMATION")
            print(f"{Fore.GREEN}{Style.BRIGHT}{'='*50}{Style.RESET_ALL}\n")
            
            # Print formatted info
            print(f"{Fore.CYAN}📋 Details:{Style.RESET_ALL}")
            for key, value in info.items():
                if value is not None:
                    key_display = key.replace('_', ' ').title()
                    print(f"  {Fore.YELLOW}{key_display}:{Style.RESET_ALL} {Fore.WHITE}{value}{Style.RESET_ALL}")
            
            # Print JSON
            print(f"\n{Fore.CYAN}{Style.BRIGHT}📄 JSON Output:{Style.RESET_ALL}")
            print(f"{Fore.WHITE}{json.dumps(info, indent=2, ensure_ascii=False)}{Style.RESET_ALL}\n")
            
        else:
            print(f"\n{Fore.RED}❌ Failed to fetch group information{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Please check:{Style.RESET_ALL}")
            print(f"  {Fore.CYAN}•{Style.RESET_ALL} The invite link/username/ID is correct")
            print(f"  {Fore.CYAN}•{Style.RESET_ALL} You have access to the group")
            print(f"  {Fore.CYAN}•{Style.RESET_ALL} Your session is valid\n")
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Operation cancelled{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error: {str(e)}{Style.RESET_ALL}")
        logger.error(f"Error in get_group_info: {e}", exc_info=True)


async def main() -> None:
    """Main async function with menu."""
    print_banner()
    
    while True:
        print_menu()
        
        try:
            choice = input(f"{Fore.GREEN}{Style.BRIGHT}Select option (1-2): {Style.RESET_ALL}").strip()
            
            if choice == '1':
                await start_fetching()
            elif choice == '2':
                await get_group_info()
            else:
                print(f"{Fore.RED}❌ Invalid option. Please select 1 or 2.{Style.RESET_ALL}\n")
                continue
            
            # Ask if user wants to continue
            print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
            try:
                continue_choice = input(f"{Fore.YELLOW}Continue? (yes/no): {Style.RESET_ALL}").strip().lower()
                if continue_choice not in ['yes', 'y']:
                    print(f"\n{Fore.CYAN}👋 Goodbye!{Style.RESET_ALL}\n")
                    break
            except (EOFError, KeyboardInterrupt):
                print(f"\n{Fore.CYAN}👋 Goodbye!{Style.RESET_ALL}\n")
                break
                
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Fore.CYAN}👋 Goodbye!{Style.RESET_ALL}\n")
            break
        except Exception as e:
            print(f"{Fore.RED}❌ Error: {str(e)}{Style.RESET_ALL}")
            logger.error(f"Error in main: {e}", exc_info=True)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}🛑 Export interrupted{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}‼️ Fatal error: {str(e)}{Style.RESET_ALL}")
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


