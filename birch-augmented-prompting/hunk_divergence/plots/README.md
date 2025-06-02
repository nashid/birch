
# Bugwise Divergence Analysis

This repository computes and visualizes divergence metrics between buggy and fixed code hunks.

## Overview

The analysis consists of two main stages:

1. **Computation** of bug-wise divergence metrics.  
2. **Visualization** of the results through curated plots.

## Repository Structure
```
.
├── compute_bugwise_total_divergence.py # Python script to compute divergence metrics
├── generate_images.sh # Shell script to run R scripts and crop plots
├── plot_divergent.R # R script for total divergence plot
├── plot_vertical_divergence_components.R # R script for component-wise divergence plots
├── bugwise_average_divergence.csv # Output CSV from Python script
└── pdfs/ # Output directory for final plots
```

## Prerequisites

Ensure the following tools are installed:

- Python ≥ 3.7  
- R ≥ 4.0 with packages: `beanplot`, `ggplot2`  
- `pdfcrop` (part of TeX Live or MiKTeX)  
- `ImageMagick` (`magick` CLI)

## Usage

### 1. Compute Bugwise Divergence

Run the Python script:

```bash
python compute_bugwise_total_divergence.py
```

This generates the file:
`bugwise_average_divergence.csv`

2. Generate Plots
Run the visualization script:
```
./generate_images.sh
```


This will:

- Call R scripts to generate:
  - Total divergence beanplot
  - Lexical, AST, Package, and combined divergence plots
  - Crop the generated PDFs using pdfcrop
  - Save the output files in ./pdfs/
  - Expected Output Files
    - `./pdfs/DivergentTotal_cropped.pdf`
    - `./pdfs/AvgLexical_cropped.pdf`
    - `./pdfs/AvgAST_cropped.pdf`
    - `./pdfs/AvgPackage_cropped.pdf`
    - `./pdfs/AvgDivergence_cropped.pdf`
