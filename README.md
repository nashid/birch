# BIRCH: Benchmarking Infrastructure for Repairing Code Hunks :rocket:

**BIRCH** is a dedicated benchmarking platform designed to address the challenges associated with evaluating the capabilities of foundation models (FMs) in multi-hunk code repair. It incorporates realistic multi-hunk bug instances from the Defects4J dataset and supports both open-source and proprietary LLMs. Additionally, Birch categorizes multi-hunk bugs based on complexity and provides a standardized interface for integrating and evaluating diverse repair techniques. This platform facilitates meaningful comparisons between LLMs and advances the state of research in multi-hunk program repair.

![BIRCH: Benchmarking Infrastructure for Repairing Code Hunks](images/birch-image.png)

This repository contains two main experiments:

1. **LLM-Only Experiment**  
   All code for the LLM-only study can be found in the  
   [`birch_llm_prompting`](./birch_llm_prompting) folder.

2. **Prompt Augmentations**  
   All code for the prompt-augmentation experiments can be found in the  
   [`birch_augmented_prompting`](./birch_augmented_prompting) folder.
