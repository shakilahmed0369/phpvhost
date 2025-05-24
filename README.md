# PHP VHost Manager 🚀

A powerful CLI tool to manage Apache virtual hosts with SSL support for PHP projects, perfect for local development environments.

## Features ✨

- 🔒 Automatic SSL certificate generation using mkcert
- 🌐 Easy virtual host configuration
- 🔄 Interactive project management
- 🔍 Fuzzy search project selection
- ⚡ Quick domain setup with .test TLD
- 🛡️ Secure by default with HTTPS
- 📝 Easy hosts file management
- 🎨 Beautiful TUI interface

## Prerequisites 📋

- Python 3.6+
- Apache HTTP Server
- Root/sudo privileges
- Linux system

## Installation 💻

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd phpvhost
   ```

2. Make the install script executable:
   ```bash
   chmod +x install.sh
   ```

3. Run the installation script:
   ```bash
   sudo ./install.sh
   ```

The installer will:
- Install required Python packages
- Install mkcert if not present
- Set up SSL certificates
- Configure the system for virtual host management
- Make the tool globally accessible

## Usage 🛠️

Run the tool by typing:
```bash
phpvhost
```

### Main Menu Options:

1. **Register New Project** 📝
   - Select a project folder
   - Configure entry point (defaults to project's public directory)
   - Auto-generates SSL certificates
   - Sets up Apache virtual host
   - Updates hosts file

2. **Manage Projects** 📋
   - List all configured projects
   - View project status
   - Remove projects and their configurations

3. **System Status** ⚙️
   - Check Apache service status
   - Verify mkcert installation
   - Count SSL certificates
   - Monitor virtual host configurations

### Command Line Usage

You can also use command line arguments:

```bash
phpvhost register  # Register a new project
phpvhost remove   # Remove an existing project
```

## Configuration 🔧

The tool stores its configuration in `~/.phpvhost_config.json`. The main configurable option is:

- `base_path`: The base directory where your PHP projects are located

## Uninstallation 🗑️

To remove PHP VHost Manager:

```bash
sudo ./install.sh uninstall
```

## Troubleshooting 🔍

1. **Apache Not Running**
   - Check Apache status: `sudo systemctl status httpd`
   - Start Apache: `sudo systemctl start httpd`

2. **SSL Certificate Issues**
   - Run `mkcert -install` manually
   - Check certificate directory: `~/.localhost-ssl`

3. **Permission Errors**
   - Ensure you're running with sudo
   - Check Apache logs: `/var/log/httpd/error_log`

## License 📄

This project is open-source and available under the MIT License.

## Contributing 🤝

Contributions are welcome! Please feel free to submit pull requests.
