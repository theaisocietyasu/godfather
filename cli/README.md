# Godfather CLI

Beautiful command-line interface for managing AI Society ASU RunPod environments.

![CLI Demo](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

- 🎨 **Beautiful Interface** - Rich terminal UI with colors, tables, and panels
- 🔐 **Secure Authentication** - Discord-based authentication
- 🚀 **Pod Management** - List and connect to available RunPod environments
- 🔌 **SSH Integration** - Automatic SSH key setup and connection
- 📊 **Status Monitoring** - Check authentication and configuration status

## 📦 Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install godfather-cli
```

### Option 2: Install from GitHub

```bash
pip install git+https://github.com/theaisocietyasu/godfather.git#subdirectory=cli
```

### Option 3: Install for Development

```bash
git clone https://github.com/theaisocietyasu/godfather.git
cd godfather/cli
pip install -e .
```

## 🚀 Quick Start

1. **Run the CLI**:

   ```bash
   godfather
   ```
2. **Authenticate**:

   - Visit the admin portal to get your authentication token
   - Paste the token when prompted
3. **Connect to a Pod**:

   - Select option `2` to connect to a pod
   - Choose from available pods
   - Automatically SSH into your isolated workspace

## 📖 Usage

### Interactive Menu

Simply run:

```bash
godfather
```

You'll see a beautiful menu:

```
╔═══════════════════════════════════════╗
║ Godfather CLI                         ║
║ AI Society RunPod Environment Manager ║
╚═══════════════════════════════════════╝

╭──────── What would you like to do? ──────────╮
│ 1.  📋 List available pods                   │
│ 2.  🔌 Connect to a pod                      │
│ 3.  📊 Show status                           │
│ 4.  🚪 Logout                                │
│ 5.  👋 Exit                                  │
╰──────────────────────────────────────────────╯
```

### Command-Line Interface

```bash
# List available pods
godfather list

# Connect to a specific pod
godfather connect <pod-id>

# Connect interactively
godfather connect

# Show CLI status
godfather status

# Logout
godfather logout

# Re-authenticate
godfather auth

# Use custom API URL
godfather --api-url https://your-api.com list
```

## 🔑 Authentication

1. Get your authentication token from: `https://your-godfather-instance.com/cli-auth`
2. Run `godfather` or `godfather auth`
3. Paste your token when prompted
4. Token is securely stored in `~/.godfather/config.json`

## 🛠️ Configuration

Configuration is stored in `~/.godfather/config.json`:

```json
{
  "token": "discord_<user_id>_<timestamp>",
  "discord_user_id": "<your_discord_id>"
}
```

## 🎨 Features in Detail

### Beautiful Tables

Pod listings display in rich, colorful tables:

```
           🚀 Available Pods (3)
╭───┬────────┬─────────────┬──────────────┬───────────╮
│ # │ Status │ Name        │ ID           │ Created   │
├───┼────────┼─────────────┼──────────────┼───────────┤
│ 1 │ 🟢 RUN │ ml-training │ abc123def... │ 2 days ago│
│ 2 │ 🟢 RUN │ gpu-dev     │ xyz789ghi... │ 1 week ago│
│ 3 │ 🔴 OFF │ testing     │ jkl456mno... │ 3 days ago│
╰───┴────────┴─────────────┴──────────────┴───────────╯
```

### Status Dashboard

```
        Godfather CLI Status
╭─────────────────────┬─────────────────────────────╮
│ 🔐 Authentication   │ ✓ Authenticated             │
│ 🌐 API Connection   │ ✓ Connected                 │
│ 🏠 Config Directory │ /home/user/.godfather       │
│ 🔗 API Endpoint     │ https://api.example.com     │
╰─────────────────────┴─────────────────────────────╯
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- [**Discord**](https://discord.gg/fXWXwz6fEG)
## 🎓 About

Built with ❤️ by [AI Society at Arizona State University](https://ais-asu.com/)
