#!/bin/bash
cd "$(dirname "$0")"
uv run python -m pdfka serve --input input/example_input.json 
