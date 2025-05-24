#!/usr/bin/env python3

import os
import sys
import subprocess
import json
from pathlib import Path
import argparse
import shutil
import platform

# Auto-install rich
try:
    from rich import print
    from rich.prompt import Prompt, Confirm
except ImportError:
    print("Installing 'rich' package...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
    from rich import print
    from rich.prompt import Prompt, Confirm

CONFIG_PATH = Path.home() / ".laravel_vhoster_config.json"
APACHE_VHOST_DIR = "/etc/httpd/conf/extra"
VHOST_INCLUDE_PATH = "/etc/httpd/conf/httpd.conf"
HOSTS_PATH = "/etc/hosts"
CERTS_PATH = Path.home() / ".localhost-ssl"

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)

def ensure_include_in_httpd():
    include_line = 'IncludeOptional conf/extra/*.conf\n'
    with open(VHOST_INCLUDE_PATH, "r") as f:
        contents = f.readlines()
    if not any("IncludeOptional conf/extra/" in line for line in contents):
        with open(VHOST_INCLUDE_PATH, "a") as f:
            f.write("\n" + include_line)
        print("[green]Added vhost include directive to httpd.conf[/green]")

def install_mkcert():
    if shutil.which("mkcert"):
        print("[green]mkcert is already installed[/green]")
        return

    os_type = platform.system().lower()
    print("[yellow]mkcert not found. Installing...[/yellow]")

    try:
        if shutil.which("brew"):
            subprocess.run(["brew", "install", "mkcert"], check=True)
        elif shutil.which("pacman"):
            subprocess.run(["sudo", "pacman", "-S", "--noconfirm", "mkcert", "nss"], check=True)
        elif shutil.which("apt"):
            subprocess.run(["sudo", "apt", "install", "-y", "libnss3-tools", "mkcert"], check=True)
        else:
            print("[red]Cannot install mkcert automatically. Please install it manually.[/red]")
            sys.exit(1)
    except Exception as e:
        print(f"[red]Failed to install mkcert: {e}[/red]")
        sys.exit(1)

def setup_mkcert_ca():
    try:
        subprocess.run(["mkcert", "-install"], check=True)
        print("[green]mkcert local CA installed[/green]")
    except Exception as e:
        print(f"[red]Failed to install mkcert CA:[/red] {e}")
        sys.exit(1)

def check_and_enable_mod_ssl():
    conf_path = Path("/etc/httpd/conf/httpd.conf")
    ssl_module_enabled = False
    if conf_path.exists():
        with open(conf_path, "r") as f:
            for line in f:
                if "LoadModule ssl_module" in line and not line.strip().startswith("#"):
                    ssl_module_enabled = True
                    break

    if ssl_module_enabled:
        print("[green]mod_ssl is already enabled[/green]")
    else:
        print("[yellow]mod_ssl not enabled. Enabling...[/yellow]")
        if shutil.which("a2enmod"):
            subprocess.run(["sudo", "a2enmod", "ssl"], check=True)
        else:
            print("[red]Please ensure mod_ssl is enabled manually (check httpd.conf)[/red]")

def generate_ssl_cert(domain):
    CERTS_PATH.mkdir(parents=True, exist_ok=True)
    cert_path = CERTS_PATH / f"{domain}.pem"
    key_path = CERTS_PATH / f"{domain}-key.pem"

    if cert_path.exists() and key_path.exists():
        print(f"[yellow]SSL cert already exists for {domain}[/yellow]")
        return cert_path, key_path

    try:
        subprocess.run(["mkcert", "-key-file", str(key_path), "-cert-file", str(cert_path), domain], check=True)
        print(f"[green]Generated SSL cert for {domain}[/green]")
        return cert_path, key_path
    except Exception as e:
        print(f"[red]Failed to generate SSL cert:[/red] {e}")
        return None, None

def create_vhost_file(domain, public_path, ssl_cert, ssl_key):
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
    print(f"[green]Virtual host (SSL + HTTP) file created:[/green] {vhost_path}")

def delete_vhost(domain):
    vhost_path = os.path.join(APACHE_VHOST_DIR, f"{domain}.conf")
    if os.path.exists(vhost_path):
        os.remove(vhost_path)
        print(f"[red]Deleted virtual host file:[/red] {vhost_path}")
    else:
        print(f"[yellow]No vhost file found for {domain}[/yellow]")

def delete_ssl_cert(domain):
    cert_path = CERTS_PATH / f"{domain}.pem"
    key_path = CERTS_PATH / f"{domain}-key.pem"

    deleted = False
    if cert_path.exists():
        cert_path.unlink()
        deleted = True
    if key_path.exists():
        key_path.unlink()
        deleted = True

    if deleted:
        print(f"[red]Deleted SSL cert and key for {domain}[/red]")

def update_hosts(domain, add=True):
    with open(HOSTS_PATH, "r") as f:
        lines = f.readlines()

    if add:
        if not any(domain in line for line in lines):
            with open(HOSTS_PATH, "a") as f:
                f.write(f"\n127.0.0.1    {domain}\n")
            print(f"[green]{domain} added to /etc/hosts[/green]")
        else:
            print(f"[yellow]{domain} already exists in /etc/hosts[/yellow]")
    else:
        new_lines = [line for line in lines if domain not in line]
        with open(HOSTS_PATH, "w") as f:
            f.writelines(new_lines)
        print(f"[red]{domain} removed from /etc/hosts[/red]")

def restart_apache():
    try:
        subprocess.run(["sudo", "systemctl", "restart", "httpd"], check=True)
        print("[bold green]Apache restarted successfully![/bold green]")
    except subprocess.CalledProcessError:
        print("[bold red]Failed to restart Apache. Check your permissions.[/bold red]")

def register_interactive(config):
    if not config.get("base_path"):
        base_path = Prompt.ask("Enter base Laravel projects path (e.g. /home/user/Projects)")
        config["base_path"] = base_path
        save_config(config)

    ensure_include_in_httpd()
    install_mkcert()
    setup_mkcert_ca()
    check_and_enable_mod_ssl()

    project_name = Prompt.ask("Enter Laravel project folder name (e.g. myapp)")
    domain = f"{project_name}.test"

    # Ask for entry point instead of assuming "public"
    entry_point = Prompt.ask("Enter the entry point path relative to base path (e.g. myapp/public)")
    public_path = os.path.join(config["base_path"], entry_point)

    if not os.path.exists(public_path):
        print(f"[bold red]Path does not exist:[/bold red] {public_path}")
        return

    cert, key = generate_ssl_cert(domain)
    if not cert or not key:
        return

    create_vhost_file(domain, public_path, cert, key)
    update_hosts(domain, add=True)
    restart_apache()
    print(f"[bold green]✔️ Visit https://{domain} in your browser![/bold green]")

def remove_interactive(config):
    project_name = Prompt.ask("Enter Laravel project folder name to remove (e.g. myapp)")
    domain = f"{project_name}.test"

    confirm = Confirm.ask(f"Are you sure you want to remove [red]{domain}[/red] with its SSL config?")
    if not confirm:
        print("[yellow]Operation cancelled.[/yellow]")
        return

    delete_vhost(domain)
    update_hosts(domain, add=False)
    delete_ssl_cert(domain)
    restart_apache()
    print(f"[bold green]✔️ Removed {domain}![/bold green]")

def main():
    if os.geteuid() != 0:
        print("[bold red]Run this script with sudo to configure Apache and /etc/hosts[/bold red]")
        print("Try: [yellow]sudo python3 laravel_vhoster.py register[/yellow]")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Laravel VHost Manager + Auto SSL")
    parser.add_argument("command", choices=["register", "remove"], help="Command to run")

    args = parser.parse_args()
    config = load_config()

    if args.command == "register":
        register_interactive(config)
    elif args.command == "remove":
        remove_interactive(config)

if __name__ == "__main__":
    main()