import os
import pickle
import argparse
from redwood.algorithms.vector_database import BuildVectorDatabase, QueryVectorDatabase, QueryVectorDatabaseRAG
from redwood.algorithms.embedding_database import QueryEmbeddingDatabaseEmb, QueryEmbeddingDatabaseEmbAST
from redwood.algorithms.ast_algorithm import load_dataset, P, BuildFullASTDataset, SerializeSubtree
from redwood.algorithms.ada_database import QueryAdaDatabaseEmb, QueryAdaDatabaseEmbAST
import json
from birch.llm.llm_api_call import invoke_llm
from birch.prompts.prompt import generate_prompt
from birch.utils.d4j_infra import concatenate_trigger_test_info, strip_code_block
from prompts.similar_result_prompts import generate_algorithm_enhanced_prompt, generate_algorithm_enhanced_prompt_feedback

def get_fix_code_algorithm(project, bug_id, bug_num, dataset, mode, model, PROMPT_PATH, GENERATED_PATCHES_PATH, MF_DATASET_PATH, API_HOST, CHECKOUT_DIR, FIXED_DIR, METHOD, FIXED_JSON, FEEDBACK, SCOPE, last_code, prompt_text=None,):
    current_bug = f"{project}_{bug_id}"
    if current_bug not in dataset:
        print(f"No buggy function found for {current_bug}")
        return None

    buggy_code_entry = dataset[current_bug]["buggy_code"][str(bug_num)]
    buggy_code = buggy_code_entry["code"]
    bug_type = dataset[current_bug]["hunk_type"]
    hunk_mapping = dataset[current_bug].get("hunk_mapping", {})

    buggy_hunks = []
    for hunk in hunk_mapping.get(str(bug_num), []):
        buggy_hunks.append(hunk["code"])

    delineated_bug_entry = dataset[current_bug]["delineated_bug"][str(bug_num)]
    delineated_bug = delineated_bug_entry["code"]
    concatenated_hunks = "\n".join(buggy_hunks)
    bug_description_title = dataset[current_bug]["bug_report"]["title"]
    bug_description = dataset[current_bug]["bug_report"]["bug_description"]
    if SCOPE == "file":
        javadoc = ""
    else:
        javadoc = delineated_bug_entry["javadoc"]
    test_info_list = concatenate_trigger_test_info(MF_DATASET_PATH, current_bug)
    test_info_str = "\n".join(
        [
            f"This code is buggy because of the following `{len(test_info_list)}` test case failure. "
            "Test code and corresponding error messages will be shown below.\n "
            f"Here is test code {i+1}:\n{test_code}\nand its corresponding error message:\n{error_msg}\n"
            for i, (test_code, error_msg) in enumerate(test_info_list)
        ]
    )

    system_prompt = "You are a Java expert tasked with code repair. Provide only the corrected code."
    if prompt_text is not None:
        prompt = prompt_text
    else:
        prompt = generate_prompt(buggy_code, delineated_bug, javadoc, bug_description_title, bug_description, test_info_str, mode, bug_type, scope="method")

    dataset = load_dataset(MF_DATASET_PATH)

    # Build the vector database from the dataset (using your existing function)
    dataset_ast = BuildFullASTDataset(dataset, P, work_dir=CHECKOUT_DIR, fixed_dir=FIXED_DIR, fixed_json=FIXED_JSON)  

    # Retrieve the query AST
    if METHOD == "ast":
        query_ast = None
        for subtree, metadata in dataset_ast:
            if metadata["bug_id"] == current_bug and metadata["hunk_index"] == str(bug_num):
                query_ast = subtree
                break

        if query_ast is None:
            print(f"Error: Query bug ID {current_bug} not found in dataset.")
        # Query the vector database to get the top-k similar bug fixes
        top_results = QueryVectorDatabase(query_ast, k=5, query_bug_id=current_bug, query_hunk_index=bug_num)  # Adjust to match your database query method

        similar_examples = []
        
        for faiss_metadata, _ in top_results:
            buggy_code_example = faiss_metadata['buggy_code']  # Access the buggy code from the metadata
            fixed_code_example = faiss_metadata['fixed_code']  # Access the fixed code from the metadata
            similar_examples.append({"buggy_code": buggy_code_example, "fixed_code": fixed_code_example})
        
        # Generate the enhanced prompt with similar examples
        if FEEDBACK:
            prompt = generate_algorithm_enhanced_prompt_feedback(similar_examples, last_code)
        else:
            prompt = generate_algorithm_enhanced_prompt(similar_examples, prompt)
    elif METHOD == "rag":
        current_bug = f"{project}_{bug_id}"
        buggy_code = buggy_code_entry["code"]

        top_results = QueryVectorDatabaseRAG(query_buggy_code=buggy_code, k=5, query_bug_id=current_bug, query_hunk_index=bug_num)

        similar_examples = []
        for rag_metadata, rag_score in top_results:
            buggy_code_example = rag_metadata.get('buggy_code', '')
            fixed_code_example = rag_metadata.get('fixed_code', '')
            similar_examples.append({
                "buggy_code": buggy_code_example,
                "fixed_code": fixed_code_example
            })
        if FEEDBACK:
            prompt = generate_algorithm_enhanced_prompt_feedback(similar_examples, last_code)
        else:
            prompt = generate_algorithm_enhanced_prompt(similar_examples, prompt)
    elif METHOD == "emb-ast":
        query_ast = None
        for subtree, metadata in dataset_ast:
            if metadata["bug_id"] == current_bug and metadata["hunk_index"] == str(bug_num):
                query_ast = subtree
                break

        if query_ast is None:
            print(f"Error: Query bug ID {current_bug} not found in dataset.")

        # Embedding-based AST approach
        top_results = QueryEmbeddingDatabaseEmbAST(
            query_subtree=query_ast,
            k=5,
            model_name="all-MiniLM-L6-v2",  # or whichever model
            db_path="embedding_db.index",   # your embedded AST index file
            query_bug_id=current_bug,
            query_hunk_index=bug_num
        )

        similar_examples = []
        for emb_metadata, emb_dist in top_results:
            buggy_code_example = emb_metadata.get('buggy_code', '')
            fixed_code_example = emb_metadata.get('fixed_code', '')
            similar_examples.append({
                "buggy_code": buggy_code_example,
                "fixed_code": fixed_code_example
            })
        if FEEDBACK:
            prompt = generate_algorithm_enhanced_prompt_feedback(similar_examples, last_code)
        else:
            prompt = generate_algorithm_enhanced_prompt(similar_examples, prompt)
    elif METHOD == "emb-rag":
        # Embedding-based code approach
        current_bug = f"{project}_{bug_id}"
        buggy_code = buggy_code_entry["code"]

        top_results = QueryEmbeddingDatabaseEmb(
            query_buggy_code=buggy_code,
            k=5,
            model_name="all-MiniLM-L6-v2",  # or whichever model
            db_path="embedding_db.index",   # your embedded code index file
            query_bug_id=current_bug,
            query_hunk_index=bug_num
        )

        similar_examples = []
        for emb_metadata, emb_dist in top_results:
            buggy_code_example = emb_metadata.get('buggy_code', '')
            fixed_code_example = emb_metadata.get('fixed_code', '')
            similar_examples.append({
                "buggy_code": buggy_code_example,
                "fixed_code": fixed_code_example
            })
        if FEEDBACK:
            prompt = generate_algorithm_enhanced_prompt_feedback(similar_examples, last_code)
        else:
            prompt = generate_algorithm_enhanced_prompt(similar_examples, prompt)

    elif METHOD == "ada-ast":
        query_ast = None
        for subtree, metadata in dataset_ast:
            if metadata["bug_id"] == current_bug and metadata["hunk_index"] == str(bug_num):
                query_ast = subtree
                break

        if query_ast is None:
            print(f"Error: Query bug ID {current_bug} not found in dataset.")

        # Embedding-based AST approach
        top_results = QueryAdaDatabaseEmbAST(
            query_subtree=query_ast,
            k=5,
            model_name='text-embedding-3-small',
            db_path="ada_db.index",   # your embedded AST index file
            query_bug_id=current_bug,
            query_hunk_index=bug_num
        )

        similar_examples = []
        for emb_metadata, emb_dist in top_results:
            buggy_code_example = emb_metadata.get('buggy_code', '')
            fixed_code_example = emb_metadata.get('fixed_code', '')
            similar_examples.append({
                "buggy_code": buggy_code_example,
                "fixed_code": fixed_code_example
            })

        if FEEDBACK:
            prompt = generate_algorithm_enhanced_prompt_feedback(similar_examples, last_code)
        else:
            prompt = generate_algorithm_enhanced_prompt(similar_examples, prompt)
    elif METHOD == "ada-rag":
        # Embedding-based code approach
        current_bug = f"{project}_{bug_id}"
        buggy_code = buggy_code_entry["code"]

        top_results = QueryAdaDatabaseEmb(
            query_buggy_code=buggy_code,
            k=5,
            model_name='text-embedding-3-small', 
            db_path="ada_db.index",   # your embedded code index file
            query_bug_id=current_bug,
            query_hunk_index=bug_num
        )

        similar_examples = []
        for emb_metadata, emb_dist in top_results:
            buggy_code_example = emb_metadata.get('buggy_code', '')
            fixed_code_example = emb_metadata.get('fixed_code', '')
            similar_examples.append({
                "buggy_code": buggy_code_example,
                "fixed_code": fixed_code_example
            })

        if FEEDBACK:
            prompt = generate_algorithm_enhanced_prompt_feedback(similar_examples, last_code)
        else:
            prompt = generate_algorithm_enhanced_prompt(similar_examples, prompt)




    if "mixtral" in model.lower():
        # Reference: https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1#instruction-format
        prompt = f"[INST]\n{prompt}[/INST]"
    elif 'llama' in model.lower():
        # Reference: https://www.llama.com/docs/model-cards-and-prompt-formats/llama3_1/#prompt-template
        prompt = f"<|start_header_id|>user<|end_header_id|>\n{prompt}<|end_of_text|>"
        system_prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{system_prompt}"
    elif 'qwen' in model.lower():
        # Reference: https://huggingface.co/TheBloke/Qwen-7B-Chat-GPTQ#prompt-template-chatml
        prompt = f"<|im_start|>user\n{prompt}<|im_end|>"
        system_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>"

    if not os.path.exists(PROMPT_PATH):
        os.makedirs(PROMPT_PATH)
    suggestion_prompt_file_path = os.path.join(PROMPT_PATH, f'{current_bug}_prompt_{mode}.txt')

    with open(suggestion_prompt_file_path, 'a', encoding='utf-8') as file:
        file.write(prompt)
        file.write("\n\n")

    fixed_code, inference_time = invoke_llm(model, system_prompt, prompt, API_HOST)
    if fixed_code is None:
        return None, inference_time, prompt

    fixed_code = strip_code_block(fixed_code)

    if not os.path.exists(GENERATED_PATCHES_PATH):
        os.makedirs(GENERATED_PATCHES_PATH)
    generated_patches_file_path = os.path.join(
        GENERATED_PATCHES_PATH, f'{current_bug}_generated_patches_{mode}.txt'
    )
    with open(generated_patches_file_path, 'a', encoding='utf-8') as file:
        file.write(fixed_code)
        file.write("\n")

    return fixed_code, inference_time, prompt
