#!/bin/bash

# WANDA Telescope Test Runner with Coverage
# This script runs all tests with coverage reporting

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run pytest with coverage
pytest --cov=camera --cov=main --cov=web --cov=session --cov-report=term-missing --cov-report=term --tb=short
