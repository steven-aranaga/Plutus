# Plutus Bitcoin Brute Forcer

A high-performance Bitcoin wallet collider that brute forces random wallet addresses with Docker support and advanced optimizations.

[![](https://img.shields.io/github/stars/Isaacdelly/Plutus.svg)](https://github.com/Isaacdelly/Plutus)

## Table of Contents
- [Quick Start](#quick-start)
- [Docker Setup (Recommended)](#docker-setup-recommended)
- [Manual Installation](#manual-installation)
- [Usage](#usage)
- [Performance Optimizations](#performance-optimizations)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
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
- System dependencies (Linux/macOS): `sudo apt-get install libgmp3-dev`
- Python packages: `pip3 install -r requirements.txt`

### Installation Steps
```bash
git clone https://github.com/steven-aranaga/Plutus.git
cd Plutus
pip3 install -r requirements.txt
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

### Performance Improvements
- **Original**: ~1,250 addresses/second
- **Optimized**: ~1,600+ addresses/second
- **With coincurve**: ~42,000+ addresses/second (25x improvement)

### Bloom Filter Support
Includes demonstration of Bloom filters for extremely large databases:
- Memory efficient probabilistic data structure
- Constant-time O(1) lookups
- Handles billions of addresses with minimal memory

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

## How It Works

### Core Algorithm
1. **Key Generation**: Generate random 32-byte private keys using `os.urandom()`
2. **Public Key Conversion**: Convert to public keys using high-performance crypto libraries
3. **Address Generation**: Create Bitcoin addresses using `binascii` and `hashlib`
4. **Database Lookup**: Check against pre-calculated database of funded addresses
5. **Result Storage**: Save found addresses to `plutus.txt`

### Database Structure
- Pre-calculated database of funded P2PKH Bitcoin addresses
- Memory-efficient suffix matching for large datasets
- Read-only mounting in Docker for safety

### Multiprocessing
- Utilizes `ThreadPoolExecutor` for concurrent processing
- Configurable CPU core usage
- Efficient task distribution and resource management

## Proof of Concept

This program attempts to find Bitcoin private keys that correlate to wallets with positive balances. It's essentially a brute forcing algorithm that:

1. Continuously generates random Bitcoin private keys
2. Converts private keys to wallet addresses
3. Checks addresses against a database of funded wallets
4. Saves any matches to `plutus.txt`

The goal is to randomly find a funded wallet out of the 2^160 possible wallets in existence.

**Note**: The probability of finding a funded wallet is astronomically low due to the vast number of possible private keys (2^256). This software is primarily for educational and research purposes.

## Legal Notice

⚠️ **Important**: This software is for educational purposes only. 

- Bitcoin brute forcing has an astronomically low probability of success
- Use responsibly and in accordance with local laws
- The authors are not responsible for any misuse of this software
- Consider the ethical implications before use

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

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/steven-aranaga/Plutus/issues)
- Documentation: See inline help with `python3 plutus.py help`
- Docker Help: Use `./start.sh --help` or `make help`
