# Contributing to Plutus

Thank you for your interest in contributing to Plutus! This document provides guidelines and instructions for contributing to the project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Contribution Workflow](#contribution-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Performance Considerations](#performance-considerations)

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. Remember that this is an educational tool, and all contributions should align with the project's educational purpose.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up your development environment (see below)
4. Create a new branch for your feature or bugfix
5. Make your changes
6. Submit a pull request

## Development Environment

### Prerequisites
- Python 3.9+
- Git
- Docker (optional, for containerized development)

### Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Plutus.git
cd Plutus

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov flake8 black

# Install the fastest cryptographic library for better performance
pip install coincurve
```

### Using Docker for Development

```bash
# Build the development container
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build

# Run in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Contribution Workflow

1. **Create a branch**: Create a new branch for your feature or bugfix
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**: Implement your feature or fix

3. **Follow coding standards**: Run linters and formatters
   ```bash
   # Format code with Black
   black *.py
   
   # Check for style issues
   flake8 *.py
   ```

4. **Test your changes**: Run tests to ensure your changes work correctly
   ```bash
   pytest
   ```

5. **Commit your changes**: Use clear commit messages
   ```bash
   git commit -m "Add feature: description of your feature"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Submit a pull request**: Go to the original repository and create a pull request

## Coding Standards

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused on a single responsibility
- Comment complex sections of code
- Use type hints where appropriate

## Testing

- Add tests for new features
- Ensure all tests pass before submitting a pull request
- Aim for good test coverage of your code

## Documentation

- Update the README.md if your changes affect usage
- Add or update docstrings for all functions and classes
- Document any new command-line options
- If adding new features, update the help text in the script

## Performance Considerations

Plutus is a performance-sensitive application. When contributing, please consider:

1. **Memory Efficiency**: The application needs to handle large datasets
   - Use generators and iterators where appropriate
   - Be mindful of memory usage when processing large files
   - Consider using memory-efficient data structures like Bloom filters

2. **CPU Efficiency**: The application performs cryptographic operations
   - Profile your code to identify bottlenecks
   - Use the fastest available libraries (coincurve preferred)
   - Consider parallelization for CPU-bound tasks

3. **Benchmarking**: Use the built-in benchmarking tools
   ```bash
   # Run the basic benchmark
   python plutus.py time
   
   # Run the extended benchmark
   python plutus.py time=extended
   
   # Run the Bloom filter benchmark
   python bloom_filter_demo.py
   ```

## Feature Ideas

If you're looking for ways to contribute, here are some ideas:

1. **Improved Database Handling**:
   - Support for more efficient database formats (SQLite, LMDB)
   - Incremental database updates
   - Compressed database storage

2. **Performance Optimizations**:
   - GPU acceleration for cryptographic operations
   - More efficient address generation algorithms
   - Advanced parallelization techniques

3. **User Interface Improvements**:
   - Progress visualization
   - Real-time statistics dashboard
   - Web interface for monitoring

4. **Additional Features**:
   - Support for more address types (P2SH, Bech32)
   - Support for other cryptocurrencies
   - Advanced search strategies beyond pure random

Thank you for contributing to Plutus!

