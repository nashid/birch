# BIRCH: Benchmarking Infrastructure for Repairing Code Hunks :rocket:

**BIRCH** is a dedicated benchmarking platform designed to address the challenges associated with evaluating the capabilities of foundation models (FMs) in multi-hunk code repair. It incorporates realistic multi-hunk bug instances from the Defects4J dataset and supports both open-source and proprietary LLMs. Additionally, Birch categorizes multi-hunk bugs based on complexity and provides a standardized interface for integrating and evaluating diverse repair techniques. This platform facilitates meaningful comparisons between LLMs and advances the state of research in multi-hunk program repair.

![BIRCH: Benchmarking Infrastructure for Repairing Code Hunks](images/birch-image.png)


### Environment Setup

Steps to set up the environment to run the framework [here](docs/env_set_up.md)

### Acquiring Defects4J Dataset

Steps to set up Defects4J [here](docs/d4j_dataset.md).


### LLM Setup
Steps to set up the LLMs can be found [here](docs/llm_setup.md)
We also provide steps to automate the process of setting up hosted LLMs using Ollama models. The framework can be executed with Ollama models, and detailed instructions are available [here](docs/ollama.md).


### Running Our Experiments

Steps to run the bug repair with Defects4J [here](docs/d4j_code_repair.md).

### Defects4J Commands

Commands about Defects4J [here](docs/defects4j_commands.md).

### Defects4J Bugs Characterization

Bug Characterization about Defects4J [here](docs/bug_char_hunk.md)

### Testing
Steps to run the bug repair with Defects4J [here](docs/unit_test.md).

### Results Directory Navigation
Steps on understanding our results can be found [here](docs/results.md).
