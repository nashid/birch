# How to Download and Run Ollama Models

To use Ollama models locally, follow these steps:

1. **Install Ollama**:

- **macOS**: Install Ollama using Homebrew:  
   ```bash
   brew install ollama
   ```

- **Windows**: Download and install Ollama from the official website:  
   [https://ollama.com](https://ollama.com).  

- **Linux**: Install using the following script:  
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Start the Ollama Service**:  
   Run the Ollama server to serve the models:  
   ```bash
   ollama serve
   ```

3. **Download Models**:  
   Use the `ollama pull` command to download specific models:
   - **Llama 3.1 (405B)**:  
     ```bash
     ollama pull llama3.1:405b
     ```
   - **Mixtral (mixtral:8x7b)**:  
     ```bash
     ollama pull mixtral:8x7b
     ```
   - **Qwen (qwen:7b)**:  
     ```bash
     ollama pull qwen:7b
     ```

4. **Verify Installation**:  
   List all downloaded models with:  
   ```bash
   ollama list
   ```

5. **Run a Model**:  
   Run and test a model locally:  
   ```bash
   ollama run llama3.1:405b
   ```

## How to Run the Ollama Setup and Script Execution

This document explains how to use the script to install **Ollama**, start the Ollama service, pull a specified model, and run the `d4j_code_repair.py` script with custom arguments using bash script `d4j_repair_ollama.sh`

---

## Overview

`d4j_repair_ollama.sh` performs the following steps:

1. Checks if **Ollama** is installed on your Linux system.
   - If not, it automatically installs `Ollama`.
2. Starts the Ollama service using `nohup` to ensure it runs in the background.
3. Pulls a specified Ollama model (e.g., `ollama/llama3.1:405b`).
4. Runs the `d4j_code_repair.py` script with the given arguments.
5. Cleans up and stops the Ollama service after the script completes.

---

## Prerequisites

Before running the script, ensure the following:

1. **Python** is installed on your system.
2. **Ollama** is compatible with your environment.
3. The `d4j_code_repair.py` script is available in the same directory or accessible path.

---

## Script Usage

To run the script, execute the following command in the terminal:

```bash
./d4j_repair_ollama.sh <model_name> <mode> <multihunk>
```

No need to specify the API host port as it is defaulted to `localhost:11434`, more information can be found [here]( https://github.com/ollama/ollama/blob/main/docs/faq.md)

Here is an example:

```bash
./d4j_repair_ollama.sh llama3.1:405b 4 yes
./d4j_repair_ollama.sh qwen2.5:7b 4 yes
```

BIRCH supports all LLMs provided by Ollama. For a complete list of supported models, visit the [Ollama Library](https://ollama.com/library).
