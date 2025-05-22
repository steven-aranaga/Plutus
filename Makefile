# Plutus Docker Makefile

.PHONY: help build run stop clean logs shell benchmark monitor setup

# Default target
help:
	@echo "Plutus Bitcoin Brute Forcer - Docker Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  setup      - Initial setup (create directories, .env file)"
	@echo "  build      - Build Docker containers"
	@echo "  run        - Run Plutus (foreground)"
	@echo "  run-bg     - Run Plutus in background"
	@echo "  monitor    - Run with monitoring service"
	@echo "  benchmark  - Run performance benchmark"
	@echo "  stop       - Stop all containers"
	@echo "  logs       - Show container logs"
	@echo "  shell      - Access container shell"
	@echo "  clean      - Remove containers and images"
	@echo "  status     - Show container status"
	@echo ""
	@echo "Configuration:"
	@echo "  Edit .env file to customize settings"
	@echo "  VERBOSE, SUBSTRING, BATCH_SIZE, CPU_COUNT"

# Initial setup
setup:
	@echo "Setting up Plutus Docker environment..."
	@mkdir -p output database
	@if [ ! -f .env ]; then cp .env.example .env; echo ".env file created"; fi
	@echo "Setup complete. Edit .env file to customize settings."

# Build containers
build:
	docker-compose build

# Run Plutus
run: setup
	docker-compose up plutus

# Run in background
run-bg: setup
	docker-compose up -d plutus
	@echo "Plutus is running in background. Use 'make logs' to view output."

# Run with monitoring
monitor: setup
	docker-compose --profile monitoring up

# Run benchmark
benchmark: setup
	docker-compose --profile benchmark run --rm plutus-benchmark

# Stop containers
stop:
	docker-compose down

# Show logs
logs:
	docker-compose logs -f plutus

# Access shell
shell:
	docker-compose exec plutus bash

# Clean up
clean:
	docker-compose down --rmi all --volumes --remove-orphans
	docker system prune -f

# Show status
status:
	docker-compose ps
	@echo ""
	@echo "Resource usage:"
	@docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || echo "No running containers"

# Quick start with custom settings
quick-start: setup build run-bg
	@echo "Plutus started in background with default settings"
	@echo "Use 'make logs' to view progress"
	@echo "Use 'make stop' to stop"

# Development mode (with source code mounting)
dev:
	@echo "Starting development mode..."
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Test configuration
test-config:
	@echo "Testing Docker Compose configuration..."
	@docker-compose config

# Show found addresses
show-results:
	@if [ -f plutus.txt ]; then \
		echo "Found addresses:"; \
		cat plutus.txt; \
	else \
		echo "No addresses found yet (plutus.txt doesn't exist)"; \
	fi

# Restart services
restart: stop run-bg

# Update and rebuild
update: clean build run-bg