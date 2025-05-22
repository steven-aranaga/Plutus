# Plutus Bitcoin Brute Forcer

A high-performance Bitcoin wallet collider that brute forces random wallet addresses with Docker support and advanced optimizations.

[![](https://img.shields.io/github/stars/Isaacdelly/Plutus.svg)](https://github.com/Isaacdelly/Plutus)

## Overview

Plutus is a proof-of-concept tool that demonstrates the process of Bitcoin private key generation and address matching. It continuously generates random Bitcoin private keys, converts them to wallet addresses, and checks if they match any addresses with positive balances in its database.

**Note**: The probability of finding a funded wallet is astronomically low (1 in 2^160) due to the vast keyspace. This software is primarily for educational and research purposes.

## Table of Contents
- [Quick Start](#quick-start)
- [Docker Setup (Recommended)](#docker-setup-recommended)
- [Manual Installation](#manual-installation)
- [Usage](#usage)
- [Performance Optimizations](#performance-optimizations)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Benchmarks](#benchmarks)
- [Troubleshooting](#troubleshooting)
- [Legal Notice](#legal-notice)

## Quick Start

### Using Docker (Recommended)
```bash
# Clone the repository
git clone https://github.com/steven-aranaga/Plutus.git
cd Plutus

# Quick start with Docker
./start.sh

# Or with monitoring
./start.sh --monitor

# Or run benchmark
./start.sh --benchmark
```

### Using Make Commands
```bash
make quick-start    # Setup and run
make run           # Run normally
make run-bg        # Run in background
make monitor       # Run with monitoring
make benchmark     # Performance test
make logs          # View logs
make stop          # Stop containers
```

### Manual Python Installation
```bash
# Install dependencies
sudo apt-get install libgmp3-dev  # Linux/macOS only
pip3 install -r requirements.txt

# Run directly
python3 plutus.py
```

## Docker Setup (Recommended)

This project includes a complete Docker Compose setup for easy deployment and management.

### Prerequisites
- Docker and Docker Compose
- At least 2GB RAM
- Bitcoin address database files

### Available Services

#### Main Service: `plutus`
```bash
docker-compose up plutus              # Run normally
docker-compose up -d plutus           # Run in background
```

#### Monitoring Service
```bash
docker-compose --profile monitoring up
```

#### Benchmark Service
```bash
docker-compose --profile benchmark run --rm plutus-benchmark
```

### Configuration

Create and edit `.env` file:
```bash
cp .env.example .env
```

Available options:
```bash
VERBOSE=0          # 0=silent, 1=print addresses
SUBSTRING=8        # Address suffix length (1-26)
BATCH_SIZE=1000    # Addresses per batch
CPU_COUNT=4        # CPU cores to use
MONITOR_INTERVAL=60 # Monitor update interval
```

### Docker File Structure
```
Plutus/
├── docker-compose.yml           # Main orchestration
├── Dockerfile                   # Container build
├── .env                         # Configuration
├── start.sh                     # Easy startup script
├── Makefile                     # Convenient commands
├── output/                      # Results (mounted)
├── database/                    # Address database (mounted)
└── plutus.txt                   # Found addresses (mounted)
```

## Manual Installation

### Dependencies
- [Python 3.9+](https://www.python.org/downloads/)
- System dependencies:
  - Linux: `sudo apt-get install libgmp3-dev`
  - macOS: `brew install gmp`
  - Windows: Use WSL or install GMP via MSYS2
- Python packages: `pip3 install -r requirements.txt`

### Installation Steps
```bash
git clone https://github.com/steven-aranaga/Plutus.git
cd Plutus
pip3 install -r requirements.txt

# For optimal performance, install coincurve
pip3 install coincurve
```

## Usage

### Command Line Options
```bash
python3 plutus.py [options]

Options:
  help                    Show help message
  time                    Run performance benchmark
  verbose=0|1            Print addresses (0=silent, 1=verbose)
  substring=1-26         Address suffix length for memory efficiency
  batch_size=N           Addresses per batch (default: 1000)
  cpu_count=N            CPU cores to use
```

### Examples
```bash
# Default run
python3 plutus.py

# Verbose mode with custom settings
python3 plutus.py verbose=1 substring=10 batch_size=500

# Performance test
python3 plutus.py time

# Use specific CPU count
python3 plutus.py cpu_count=8
```

## Performance Optimizations

### High-Performance Cryptography
The optimized version uses the fastest available cryptographic libraries:

| Library | Performance | Notes |
|---------|-------------|-------|
| **coincurve** | ~42,000 addr/sec | Primary choice (25x faster than fastecdsa) |
| fastecdsa | ~1,700 addr/sec | Fallback option |
| starkbank-ecdsa | ~900,000 addr/sec* | Fastest but less reliable |

*Raw benchmark performance; actual performance may vary

### Key Optimizations
1. **Batch Processing**: Process multiple addresses simultaneously
2. **Advanced Multiprocessing**: ThreadPoolExecutor for better resource management
3. **Optimized Database Loading**: Parallel file processing with memory efficiency
4. **Efficient Address Verification**: Chunk-based reading with preliminary checks
5. **Memory Management**: Configurable substring matching to reduce RAM usage
6. **Bloom Filter Support**: Optional probabilistic data structure for faster lookups

### Performance Improvements
- **Original**: ~1,250 addresses/second
- **Optimized**: ~1,600+ addresses/second
- **With coincurve**: ~42,000+ addresses/second (25x improvement)

## Architecture

### Core Components
1. **Key Generator**: Creates random private keys using cryptographically secure random number generation
2. **Cryptographic Engine**: Converts private keys to public keys using optimized libraries
3. **Address Converter**: Transforms public keys into Bitcoin addresses
4. **Database Checker**: Verifies if generated addresses exist in the database
5. **Result Manager**: Saves and reports found addresses

### Data Flow
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Random Private │     │  Public Key     │     │  Bitcoin        │
│  Key Generation ├────►│  Conversion     ├────►│  Address        │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Save Results   │     │  Check Database │     │  Address        │
│  if Match Found │◄────┤  for Match      │◄────┤  Validation     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Parallelization Strategy
- **ThreadPoolExecutor**: Manages a pool of worker threads for concurrent processing
- **Batch Processing**: Groups operations for better efficiency
- **Resource Management**: Configurable CPU core usage and memory limits

## Configuration

### Memory Efficiency
The `substring` parameter controls memory usage vs. accuracy:
- Higher values = more memory, fewer false positives
- Lower values = less memory, more false positives
- Recommended: 8 (default) for good balance
- False positive probability: 1/(16^substring)

### Resource Management
- **Batch Size**: Larger batches = better performance, more memory
- **CPU Count**: More cores = faster processing, more resource usage
- **Substring Length**: Affects memory usage and accuracy

### Database Configuration
The database consists of text files containing Bitcoin addresses with positive balances:
- Located in the `database/` directory
- Split into multiple files for GitHub compatibility
- Currently contains over 43 million addresses
- Updated periodically from http://addresses.loyce.club/

## Benchmarks

### System Requirements
For optimal performance:
- 4+ CPU cores
- 4GB+ RAM
- SSD storage for database files

### Performance Metrics
Typical performance on a modern system (Ryzen 7, 16GB RAM):

| Configuration | Addresses/Second | Memory Usage |
|---------------|------------------|-------------|
| Default | ~42,000 | ~500MB |
| With Bloom Filter | ~60,000 | ~1GB |
| High Memory Mode | ~65,000 | ~2GB |

## Troubleshooting

### Docker Issues
```bash
# View logs
docker-compose logs plutus

# Check container status
docker-compose ps

# Restart services
docker-compose restart

# Clean rebuild
docker-compose down --rmi all && docker-compose up --build
```

### Performance Issues
- Reduce `BATCH_SIZE` if running out of memory
- Reduce `SUBSTRING` length for lower memory usage
- Ensure database files are on fast storage (SSD)
- Monitor resource usage with `docker stats`

### Common Problems
1. **Out of memory**: Reduce batch size or substring length
2. **Database not found**: Ensure database files exist in `database/` directory
3. **Permission errors**: Check file permissions on mounted volumes
4. **Slow performance**: Install `coincurve` library for 25x speed improvement
5. **Import errors**: Ensure all dependencies are installed correctly

### Cryptography Library Issues
If you encounter issues with cryptographic libraries:
```bash
# Install coincurve (recommended)
pip install coincurve

# If coincurve fails, try fastecdsa
pip install fastecdsa

# Last resort
pip install starkbank-ecdsa
```

## Legal Notice

⚠️ **Important**: This software is for educational purposes only. 

- Bitcoin brute forcing has an astronomically low probability of success
- Use responsibly and in accordance with local laws
- The authors are not responsible for any misuse of this software
- Consider the ethical implications before use

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/steven-aranaga/Plutus/issues)
- Documentation: See inline help with `python3 plutus.py help`
- Docker Help: Use `./start.sh --help` or `make help`

