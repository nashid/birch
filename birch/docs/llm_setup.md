# LLM Models

This document provides instructions on configuring and running LLM models.

### Locally Hosted Open-Source Models

Steps to download `ollama` models and to run our framework can be found [here](ollama.md)

If a model is hosted locally, we need their respective API base URLs to be specified in the code:

For example, for invoking locally hosted Llama 3.1 model:
   - Pass in the API-base URL via command-line argument --api_host.
   - `python d4j_code_repair.py --mode <mode> --model ollama/llama3.1:405b --baseline yes --api_host <URL>`

Ensure that the services for these models are running locally before attempting to make any requests.

We also provide a script named `d4j_repair_ollama.sh`, which automates the following tasks:  

1. Installs Ollama.  
2. Starts the Ollama service.  
3. Pulls a specified model.  
4. Runs the `d4j_code_repair.py` script using the specified Ollama model.  

For more details, refer to the [script usage documentation](ollama.md#script-usage).


### Proprietary Models - OpenAI, Anthropic

### Storing API Keys in a `.env` File
To enhance security, store your API keys in a `.env` file. For example:

1. **OpenAI**
.env file for using OpenAI:
```python
OPENAI_API_KEY=your-openai-api-key
```

2. **Anthropic**
.env file for using Anthropic:
```python
ANTHROPIC_API_KEY=your-anthropic-api-key
```
