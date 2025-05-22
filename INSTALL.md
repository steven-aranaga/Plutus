# Installation Guide for Plutus

This guide provides detailed installation instructions for different operating systems.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Linux Installation](#linux-installation)
- [macOS Installation](#macos-installation)
- [Windows Installation](#windows-installation)
- [Docker Installation](#docker-installation)
- [Verifying Installation](#verifying-installation)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git (for cloning the repository)
- System-specific dependencies (see below)

## Linux Installation

### Ubuntu/Debian

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip libgmp3-dev build-essential git

# Clone the repository
git clone https://github.com/steven-aranaga/Plutus.git
cd Plutus

# Install Python dependencies
pip3 install -r requirements.txt

# Install coincurve for optimal performance
pip3 install coincurve
```

### Fedora/CentOS/RHEL

```bash
# Install system dependencies
sudo dnf install -y python3-devel python3-pip gmp-devel gcc gcc-c++ make git

# Clone the repository
git clone https://github.com/steven-aranaga/Plutus.git
cd Plutus

# Install Python dependencies
pip3 install -r requirements.txt

# Install coincurve for optimal performance
pip3 install coincurve
```

### Arch Linux

```bash
# Install system dependencies
sudo pacman -S python python-pip gmp gcc make git

# Clone the repository
git clone https://github.com/steven-aranaga/Plutus.git
cd Plutus

# Install Python dependencies
pip install -r requirements.txt

# Install coincurve for optimal performance
pip install coincurve
```

## macOS Installation

### Using Homebrew

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install system dependencies
brew install python3 gmp

# Clone the repository
git clone https://github.com/steven-aranaga/Plutus.git
cd Plutus

# Install Python dependencies
pip3 install -r requirements.txt

# Install coincurve for optimal performance
pip3 install coincurve
```

## Windows Installation

### Using WSL (Recommended)

Windows Subsystem for Linux provides the best compatibility:

1. Install WSL by following [Microsoft's instructions](https://docs.microsoft.com/en-us/windows/wsl/install)
2. Open a WSL terminal and follow the Linux installation instructions above

### Using Native Windows

```bash
# Install Python from https://www.python.org/downloads/windows/
# Make sure to check "Add Python to PATH" during installation

# Install Git from https://git-scm.com/download/win

# Open Command Prompt as Administrator

# Clone the repository
git clone https://github.com/steven-aranaga/Plutus.git
cd Plutus

# Install Python dependencies
pip install -r requirements.txt

# Note: coincurve may be difficult to install on Windows
# Try installing it with:
pip install coincurve
# If that fails, the program will fall back to other libraries
```

## Docker Installation

Docker provides the easiest and most consistent installation experience:

```bash
# Install Docker and Docker Compose for your platform
# https://docs.docker.com/get-docker/

# Clone the repository
git clone https://github.com/steven-aranaga/Plutus.git
cd Plutus

# Start with Docker
./start.sh

# Or use Docker Compose directly
docker-compose up
```

## Verifying Installation

To verify that everything is installed correctly:

```bash
# Run the benchmark
python3 plutus.py time

# You should see output showing the performance of your system
# If coincurve is installed correctly, you'll see much higher performance
```

## Troubleshooting

### Common Issues

#### Missing GMP Library
Error: `fatal error: gmp.h: No such file or directory`

Solution:
- Linux: `sudo apt-get install libgmp3-dev` (Ubuntu/Debian) or `sudo dnf install gmp-devel` (Fedora)
- macOS: `brew install gmp`
- Windows: Use WSL or install via MSYS2

#### Coincurve Installation Fails
Error: `error: command 'gcc' failed with exit status 1`

Solution:
- Ensure you have a C compiler installed
- Linux: `sudo apt-get install build-essential`
- macOS: `xcode-select --install`
- Windows: Install Visual C++ Build Tools or use WSL

#### Permission Errors
Error: `Permission denied` when running scripts

Solution:
```bash
# Make scripts executable
chmod +x start.sh
chmod +x *.py
```

#### Database Not Found
Error: `No such file or directory: 'database/...'`

Solution:
```bash
# Create the database directory
mkdir -p database/11_13_2022
# Download the database files from the source mentioned in database/README.md
```

### Getting Help

If you encounter issues not covered here:
1. Check the [GitHub Issues](https://github.com/steven-aranaga/Plutus/issues) for similar problems
2. Run `python3 plutus.py help` for command-line options
3. Open a new issue with details about your problem

