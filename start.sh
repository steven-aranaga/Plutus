#!/bin/bash

# Plutus Docker Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if database directory exists
if [ ! -d "database" ]; then
    print_warning "Database directory not found. Creating empty database directory."
    mkdir -p database
    print_warning "Please add Bitcoin address database files to the 'database' directory."
fi

# Create output directory if it doesn't exist
if [ ! -d "output" ]; then
    print_status "Creating output directory..."
    mkdir -p output
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file from template..."
    cp .env.example .env
    print_success ".env file created. You can edit it to customize settings."
fi

# Parse command line arguments
MODE="default"
PROFILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--monitor)
            MODE="monitor"
            PROFILE="--profile monitoring"
            shift
            ;;
        -b|--benchmark)
            MODE="benchmark"
            PROFILE="--profile benchmark"
            shift
            ;;
        -r|--randstorm)
            MODE="randstorm"
            PROFILE="--profile randstorm"
            shift
            ;;
        -d|--daemon)
            DAEMON="-d"
            shift
            ;;
        -h|--help)
            echo "Plutus Docker Startup Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -m, --monitor     Run with monitoring service"
            echo "  -b, --benchmark   Run benchmark test"
            echo "  -r, --randstorm   Run Randstorm exploit for BitcoinJS wallets"
            echo "  -d, --daemon      Run in background (daemon mode)"
            echo "  -h, --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                # Run normally"
            echo "  $0 -d             # Run in background"
            echo "  $0 -m             # Run with monitoring"
            echo "  $0 -b             # Run benchmark"
            echo "  $0 -r             # Run Randstorm exploit"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use -h or --help for usage information."
            exit 1
            ;;
    esac
done

# Display configuration
print_status "Starting Plutus Bitcoin Brute Forcer..."
print_status "Mode: $MODE"

if [ -f ".env" ]; then
    print_status "Configuration from .env:"
    grep -E "^[A-Z_]+=.*" .env | while read line; do
        echo "  $line"
    done
fi

# Build and start containers
print_status "Building Docker containers..."
if ! docker-compose build; then
    print_error "Failed to build Docker containers."
    exit 1
fi

print_success "Docker containers built successfully."

case $MODE in
    "monitor")
        print_status "Starting Plutus with monitoring..."
        docker-compose $PROFILE up $DAEMON
        ;;
    "benchmark")
        print_status "Running Plutus benchmark..."
        docker-compose $PROFILE run --rm plutus-benchmark
        ;;
    "randstorm")
        print_status "Running Randstorm exploit..."
        docker-compose $PROFILE run --rm plutus-randstorm
        ;;
    *)
        print_status "Starting Plutus..."
        docker-compose up $DAEMON plutus
        ;;
esac

if [ "$DAEMON" = "-d" ]; then
    print_success "Plutus is running in the background."
    print_status "Use 'docker-compose logs -f plutus' to view logs."
    print_status "Use 'docker-compose down' to stop."
else
    print_success "Plutus has finished running."
fi
