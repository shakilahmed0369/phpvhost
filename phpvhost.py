#!/usr/bin/env python3

"""
PHP VHost Manager
A powerful CLI tool to manage Apache virtual hosts with SSL support for PHP projects.

Author: Shakil Ahmed
Website: https://shakilahmeed.com
Email: sakilhossain01969@gmail.com
Created: May 2025
License: MIT
"""

from pathlib import Path
import os
import sys
import subprocess
import json
import shutil
import platform
import time
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator

# Configuration
CONFIG_PATH = Path.home() / ".phpvhost_config.json"
APACHE_VHOST_DIR = "/etc/httpd/conf/extra"
VHOST_INCLUDE_PATH = "/etc/httpd/conf/httpd.conf"
HOSTS_PATH = "/etc/hosts"
CERTS_PATH = Path.home() / ".localhost-ssl"

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    CLEAR_LINE = '\033[2K'
    MOVE_UP = '\033[A'

class UI:
    """Simple UI utilities"""
    
    @staticmethod
    def clear_screen():
        os.system('clear' if os.name == 'posix' else 'cls')
    
    @staticmethod
    def print_header(title):
        print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{title.center(60)}{Colors.END}")
        print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")
    
    @staticmethod
    def print_success(message):
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
    
    @staticmethod
    def print_error(message):
        print(f"{Colors.RED}❌ {message}{Colors.END}")
    
    @staticmethod
    def print_warning(message):
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")
    
    @staticmethod
    def print_info(message):
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")
    
    @staticmethod
    def print_menu_item(number, title, description=""):
        desc = f" - {description}" if description else ""
        print(f"{Colors.CYAN}{number}.{Colors.END} {Colors.BOLD}{title}{Colors.END}{desc}")
    
    @staticmethod
    def get_input(prompt, default=""):
        try:
            default_text = f" [{default}]" if default else ""
            return input(f"{Colors.YELLOW}{prompt}{default_text}: {Colors.END}").strip() or default
        except KeyboardInterrupt:
            print()  # Add a newline after ^C
            raise
    
    @staticmethod
    def get_confirmation(message):
        while True:
            response = input(f"{Colors.YELLOW}{message} (y/N): {Colors.END}").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no', '']:
                return False
            else:
                print(f"{Colors.RED}Please enter 'y' or 'n'{Colors.END}")
    
    @staticmethod
    def show_loading(message, duration=1):
        print(f"{Colors.BLUE}{message}", end="", flush=True)
        for _ in range(3):
            time.sleep(duration/3)
            print(".", end="", flush=True)
        print(f" Done!{Colors.END}")
    
    @staticmethod
    def draw_box(content, width=60):
        """Draw a box around content"""
        lines = content.split('\n')
        print(f"{Colors.CYAN}┌{'─' * (width-2)}┐{Colors.END}")
        for line in lines:
            padding = width - len(line) - 4
            print(f"{Colors.CYAN}│{Colors.END} {line}{' ' * padding} {Colors.CYAN}│{Colors.END}")
        print(f"{Colors.CYAN}└{'─' * (width-2)}┘{Colors.END}")

class PHPVHostManager:
    """Main application class"""
    
    def __init__(self):
        self.config = self.load_config()

    def select_project_folder(self, base_path):
        """Interactive folder selection with search functionality"""
        try:
            # Get all folders in the base path
            folders = [d for d in Path(base_path).iterdir() if d.is_dir()]
            
            if not folders:
                UI.print_warning(f"No folders found in {base_path}")
                return None
            
            # Create choices list with folder names and full paths
            choices = [
                Choice(value=str(folder), name=folder.name)
                for folder in sorted(folders, key=lambda x: x.name.lower())
            ]
            
            # Add separators for better visual organization
            if len(choices) > 10:
                mid = len(choices) // 2
                choices.insert(mid, Separator())
            
            # Show interactive folder selector
            selected = inquirer.fuzzy(
                message="Select a project folder:",
                choices=choices,
                validate=lambda x: True if x else "Please select a folder",
                instruction="(Use arrow keys and type to search)",
                long_instruction="Type to search, ↑↓ to navigate, Enter to select",
                max_height="70%"
            ).execute()
            
            return Path(selected).name if selected else None
            
        except Exception as e:
            UI.print_error(f"Error during folder selection: {str(e)}")
            return None

    def load_config(self):
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                return json.load(f)
        return {}

    def save_config(self, config):
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)

    def main_menu(self):
        """Display main menu and handle user selection"""
        while True:
            try:
                UI.clear_screen()
                UI.print_header("🚀 PHP VHost Manager")
                
                print(f"{Colors.MAGENTA}Easily manage PHP virtual hosts with SSL support{Colors.END}")
                print(f"{Colors.MAGENTA}Perfect for local development environments{Colors.END}\n")
                
                UI.print_menu_item("1", "📝 Register New Project", "Add a new Laravel project")
                UI.print_menu_item("2", "📋 Manage Projects", "View and remove existing projects")
                UI.print_menu_item("3", "⚙️  System Status", "Check system configuration")
                UI.print_menu_item("4", "❌ Exit", "Quit the application")
                
                print()
                choice = UI.get_input("Select an option (1-4)")
                
                if choice == "1":
                    self.register_project()
                elif choice == "2":
                    self.manage_projects()
                elif choice == "3":
                    self.show_system_status()
                elif choice == "4":
                    UI.print_info("Goodbye! 👋")
                    break
                else:
                    UI.print_error("Invalid option. Please select 1-4.")
                    time.sleep(1)
            except KeyboardInterrupt:
                print()  # Add a newline after ^C
                UI.print_info("Goodbye! 👋")
                break

    def register_project(self):
        """Register a new Laravel project"""
        UI.clear_screen()
        UI.print_header("📝 Register New PHP Project")
        
        # Get base path
        if not self.config.get("base_path"):
            print(f"{Colors.YELLOW}First time setup - please configure your base PHP projects path{Colors.END}")
            base_path = UI.get_input("Enter base PHP projects path", str(Path.home() / "Projects"))
            self.config["base_path"] = base_path
            self.save_config(self.config)
        else:
            base_path = self.config["base_path"]
            change_path = UI.get_confirmation(f"Current base path: {base_path}\nChange it?")
            if change_path:
                base_path = UI.get_input("Enter new base path", base_path)
                self.config["base_path"] = base_path
                self.save_config(self.config)
        
        # Get project details using interactive selection
        print()
        project_name = self.select_project_folder(base_path)
        if not project_name:
            UI.print_error("Project selection cancelled!")
            input("Press Enter to continue...")
            return
        
        entry_point = UI.get_input("Enter entry point relative to base path", f"{project_name}/public")
        full_path = os.path.join(base_path, entry_point)
        domain = f"{project_name}.test"
        
        # Show preview
        print()
        UI.draw_box(f"Preview:\nDomain: https://{domain}\nPath: {full_path}", 70)
        
        if not os.path.exists(full_path):
            UI.print_error(f"Path does not exist: {full_path}")
            input("Press Enter to continue...")
            return
        
        if not UI.get_confirmation("Proceed with registration?"):
            return
        
        # Perform registration 
        try:
            UI.show_loading("Setting up prerequisites")
            self.setup_prerequisites()
            
            UI.show_loading("Generating SSL certificate")
            cert, key = self.generate_ssl_cert(domain)
            
            if not cert or not key:
                UI.print_error("Failed to generate SSL certificate")
                input("Press Enter to continue...")
                return
            
            UI.show_loading("Creating virtual host configuration")
            self.create_vhost_file(domain, full_path, cert, key)
            
            UI.show_loading("Updating hosts file")
            self.update_hosts(domain, add=True)
            
            UI.show_loading("Restarting Apache")
            self.restart_apache()
            
            print()
            UI.print_success(f"🎉 {domain} registered successfully!")
            UI.print_info(f"Visit https://{domain} in your browser")
            
        except Exception as e:
            UI.print_error(f"Registration failed: {str(e)}")
        
        input("\nPress Enter to continue...")

    def manage_projects(self):
        """Manage existing projects"""
        UI.clear_screen()
        UI.print_header("📋 Manage PHP Projects")
        
        projects = self.get_existing_projects()
        
        if not projects:
            UI.print_warning("No PHP projects found")
            input("Press Enter to continue...")
            return
        
        print(f"{Colors.BOLD}Existing Projects:{Colors.END}\n")
        
        # Display projects table
        print(f"{Colors.CYAN}{'#':<3} {'Domain':<25} {'SSL':<5} {'Status':<10} {'Path'}{Colors.END}")
        print(f"{Colors.CYAN}{'-'*80}{Colors.END}")
        
        for i, project in enumerate(projects, 1):
            domain, path, ssl_status, status = project
            ssl_icon = "✅" if ssl_status else "❌"
            status_color = Colors.GREEN if status == "Active" else Colors.RED
            print(f"{i:<3} {domain:<25} {ssl_icon:<5} {status_color}{status:<10}{Colors.END} {path}")
        
        print()
        selection = UI.get_input("Enter project number to remove (or press Enter to go back)")
        
        if not selection:
            return
        
        try:
            index = int(selection) - 1
            if 0 <= index < len(projects):
                domain = projects[index][0]
                if UI.get_confirmation(f"Remove {domain} and its SSL configuration?"):
                    self.remove_project(domain)
            else:
                UI.print_error("Invalid project number")
        except ValueError:
            UI.print_error("Please enter a valid number")
        
        input("Press Enter to continue...")

    def remove_project(self, domain):
        """Remove a project"""
        try:
            UI.show_loading("Removing virtual host")
            self.delete_vhost(domain)
            
            UI.show_loading("Updating hosts file")
            self.update_hosts(domain, add=False)
            
            UI.show_loading("Removing SSL certificate")
            self.delete_ssl_cert(domain)
            
            UI.show_loading("Restarting Apache")
            self.restart_apache()
            
            UI.print_success(f"✅ Removed {domain} successfully!")
            
        except Exception as e:
            UI.print_error(f"Failed to remove {domain}: {str(e)}")

    def show_system_status(self):
        """Show system status"""
        UI.clear_screen()
        UI.print_header("⚙️ System Status")
        
        status_items = []
        
        # Check Apache
        try:
            subprocess.run(["systemctl", "is-active", "httpd"], check=True, capture_output=True)
            status_items.append(("Apache Service", "✅ Running", Colors.GREEN))
        except:
            status_items.append(("Apache Service", "❌ Not Running", Colors.RED))
        
        # Check mkcert
        if shutil.which("mkcert"):
            status_items.append(("mkcert", "✅ Installed", Colors.GREEN))
        else:
            status_items.append(("mkcert", "❌ Not Installed", Colors.RED))
        
        # Check SSL certificates
        if CERTS_PATH.exists():
            cert_count = len(list(CERTS_PATH.glob("*.pem")))
            status_items.append(("SSL Certificates", f"📁 {cert_count} found", Colors.BLUE))
        else:
            status_items.append(("SSL Certificates", "📁 No directory", Colors.YELLOW))
        
        # Check virtual hosts
        if os.path.exists(APACHE_VHOST_DIR):
            vhost_count = len([f for f in os.listdir(APACHE_VHOST_DIR) if f.endswith('.conf')])
            status_items.append(("Virtual Hosts", f"🌐 {vhost_count} configured", Colors.BLUE))
        else:
            status_items.append(("Virtual Hosts", "🌐 No directory", Colors.YELLOW))
        
        # Display status
        for item, status, color in status_items:
            print(f"{Colors.BOLD}{item:<20}{Colors.END} {color}{status}{Colors.END}")
        
        input("\nPress Enter to continue...")

    def get_existing_projects(self):
        """Get list of existing projects"""
        projects = []
        
        if not os.path.exists(APACHE_VHOST_DIR):
            return projects
        
        for file in os.listdir(APACHE_VHOST_DIR):
            if file.endswith('.conf') and '.test' in file:
                domain = file.replace('.conf', '')
                vhost_path = os.path.join(APACHE_VHOST_DIR, file)
                
                # Extract document root
                doc_root = "Unknown"
                ssl_status = False
                
                try:
                    with open(vhost_path, 'r') as f:
                        content = f.read()
                        for line in content.split('\n'):
                            if 'DocumentRoot' in line:
                                doc_root = line.split('"')[1] if '"' in line else line.split()[1]
                                break
                        ssl_status = 'SSLEngine on' in content
                except Exception:
                    pass
                
                # Check if path exists
                status = "Active" if os.path.exists(doc_root) else "Missing"
                projects.append((domain, doc_root, ssl_status, status))
        
        return projects

    # Core functionality methods (same as original script)
    def setup_prerequisites(self):
        self.ensure_include_in_httpd()
        self.install_mkcert()
        self.setup_mkcert_ca()
        self.check_and_enable_mod_ssl()

    def ensure_include_in_httpd(self):
        include_line = 'IncludeOptional conf/extra/*.conf\n'
        with open(VHOST_INCLUDE_PATH, "r") as f:
            contents = f.readlines()
        if not any("IncludeOptional conf/extra/" in line for line in contents):
            with open(VHOST_INCLUDE_PATH, "a") as f:
                f.write("\n" + include_line)

    def install_mkcert(self):
        if shutil.which("mkcert"):
            return
        
        try:
            if shutil.which("brew"):
                subprocess.run(["brew", "install", "mkcert"], check=True)
            elif shutil.which("pacman"):
                subprocess.run(["sudo", "pacman", "-S", "--noconfirm", "mkcert", "nss"], check=True)
            elif shutil.which("apt"):
                subprocess.run(["sudo", "apt", "install", "-y", "libnss3-tools", "mkcert"], check=True)
        except Exception:
            pass

    def setup_mkcert_ca(self):
        try:
            subprocess.run(["mkcert", "-install"], check=True)
        except Exception:
            pass

    def check_and_enable_mod_ssl(self):
        if shutil.which("a2enmod"):
            try:
                subprocess.run(["sudo", "a2enmod", "ssl"], check=True)
            except Exception:
                pass

    def generate_ssl_cert(self, domain):
        CERTS_PATH.mkdir(parents=True, exist_ok=True)
        cert_path = CERTS_PATH / f"{domain}.pem"
        key_path = CERTS_PATH / f"{domain}-key.pem"

        if cert_path.exists() and key_path.exists():
            return cert_path, key_path

        try:
            subprocess.run(["mkcert", "-key-file", str(key_path), "-cert-file", str(cert_path), domain], check=True)
            return cert_path, key_path
        except Exception:
            return None, None

    def create_vhost_file(self, domain, public_path, ssl_cert, ssl_key):
        vhost_config = f"""
<VirtualHost *:80>
    ServerName {domain}
    DocumentRoot "{public_path}"
    <Directory "{public_path}">
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>

<VirtualHost *:443>
    ServerName {domain}
    DocumentRoot "{public_path}"

    SSLEngine on
    SSLCertificateFile "{ssl_cert}"
    SSLCertificateKeyFile "{ssl_key}"

    <Directory "{public_path}">
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
"""
        vhost_path = os.path.join(APACHE_VHOST_DIR, f"{domain}.conf")
        with open(vhost_path, "w") as f:
            f.write(vhost_config.strip())

    def delete_vhost(self, domain):
        vhost_path = os.path.join(APACHE_VHOST_DIR, f"{domain}.conf")
        if os.path.exists(vhost_path):
            os.remove(vhost_path)

    def delete_ssl_cert(self, domain):
        cert_path = CERTS_PATH / f"{domain}.pem"
        key_path = CERTS_PATH / f"{domain}-key.pem"

        if cert_path.exists():
            cert_path.unlink()
        if key_path.exists():
            key_path.unlink()

    def update_hosts(self, domain, add=True):
        with open(HOSTS_PATH, "r") as f:
            lines = f.readlines()

        if add:
            if not any(domain in line for line in lines):
                with open(HOSTS_PATH, "a") as f:
                    f.write(f"\n127.0.0.1    {domain}\n")
        else:
            new_lines = [line for line in lines if domain not in line]
            with open(HOSTS_PATH, "w") as f:
                f.writelines(new_lines)

    def restart_apache(self):
        try:
            subprocess.run(["sudo", "systemctl", "restart", "httpd"], check=True)
        except subprocess.CalledProcessError:
            pass

def main():
    """Main entry point"""
    try:
        # Check for root privileges
        if os.geteuid() != 0:
            print(f"{Colors.RED}{Colors.BOLD}❌ This script requires root privileges{Colors.END}")
            print(f"{Colors.YELLOW}Please run with sudo:{Colors.END}")
            print(f"{Colors.CYAN}sudo python3 {sys.argv[0]}{Colors.END}")
            sys.exit(1)
        
        # Handle command line arguments for backward compatibility
        if len(sys.argv) > 1:
            if sys.argv[1] == "register":
                manager = PHPVHostManager()
                manager.register_project()
            elif sys.argv[1] == "remove":
                manager = PHPVHostManager()
                manager.manage_projects()
            else:
                print(f"{Colors.RED}Unknown command: {sys.argv[1]}{Colors.END}")
                print(f"{Colors.YELLOW}Usage: {sys.argv[0]} [register|remove]{Colors.END}")
        else:
            # Run interactive TUI
            manager = PHPVHostManager()
            manager.main_menu()
    except KeyboardInterrupt:
        print()  # Add a newline after ^C
        print(f"{Colors.BLUE}ℹ️  Program terminated by user{Colors.END}")
        sys.exit(0)

if __name__ == "__main__":
    main()