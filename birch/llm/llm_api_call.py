import json
import time
import traceback

import litellm
from litellm import APIConnectionError, BadRequestError

from llm.models import Models
import os
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

def handle_errors(e):
    if hasattr(e, 'http_status'):
        if e.http_status == 400:
            return "BadRequestError", str(e)
        elif e.http_status == 401:
            return "AuthenticationError", str(e)
        elif e.http_status == 403:
            return "PermissionDeniedError", str(e)
        elif e.http_status == 404:
            return "NotFoundError", str(e)
        elif e.http_status == 422:
            return "UnprocessableEntityError", str(e)
        elif e.http_status == 429:
            return "RateLimitError", str(e)
        elif e.http_status >= 500:
            return "InternalServerError", str(e)
    if hasattr(e, 'code') and e.code == "context_window_exceeded":
        return "ContextWindowExceededError", str(e)
    if hasattr(e, 'code') and e.code == "content_policy_violation":
        return "ContentPolicyViolationError", str(e)
    return "APIConnectionError", str(e)


def invoke_llm(model_name,
               system_prompt,
               user_prompt,
               api_host=None,
               temperature=0,
               max_tokens=4096,
               top_p=1, frequency_penalty=0, presence_penalty=0):
    attempt = 0
    backoff = 60  # Initial backoff duration in seconds
    max_cumulative_backoff = 600  # Maximum cumulative backoff time in seconds (e.g., 100 minutes)
    cumulative_backoff = 0
        
    if "gpt" in model_name.lower():
        if not openai_api_key:
            raise ValueError("Missing OPENAI_API_KEY in the environment.")
        os.environ["OPENAI_API_KEY"] = openai_api_key
    elif "claude" in model_name.lower():
        if not anthropic_api_key:
            raise ValueError("Missing ANTHROPIC_API_KEY in the environment.")
        os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    while True:
        try:
            start_time = time.time()
            if api_host:
                response = litellm.completion(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    top_p=top_p,
                    api_base=api_host
                )
            else:
                response = litellm.completion(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    top_p=top_p
                )
            end_time = time.time()
            inference_time_ms = (end_time - start_time) * 1000
            completion = response.choices[0].message.content
            print("Completion obtained")
            return completion, inference_time_ms
        except BadRequestError as e:
            if 'maximum context length' in e.message.lower():
                print(f"Error: {e.message}")
                return "Context limit exceeded", 0
            else:
                print(f"BadRequestError occurred: {e.message}")
                return None, 0
        except Exception as e:
            error_type, error_message = handle_errors(e)
            print(f"Error Type: {error_type}")
            print(f"Error Message: {error_message}")

            if isinstance(e, json.JSONDecodeError):
                print("JSON decoding error")
            elif isinstance(e, KeyError):
                print("Key error")

            # Handle specific error actions
            if error_type == "RateLimitError":
                wait_time = backoff * (2 ** attempt)  # Exponential backoff
                cumulative_backoff += wait_time

                if cumulative_backoff >= max_cumulative_backoff:
                    print("Maximum cumulative backoff time exceeded. Aborting.")
                    break

                print(f"Rate limit exceeded, retrying in {wait_time:.2f} seconds...")
                print("Traceback:")
                traceback.print_exc()
                time.sleep(wait_time)
                attempt += 1
            elif error_type == "APIConnectionError":
                wait_time = backoff * (2 ** attempt)  # Exponential backoff
                cumulative_backoff += wait_time

                if cumulative_backoff >= max_cumulative_backoff:
                    print("Maximum cumulative backoff time exceeded. Aborting.")
                    break

                print(f"APIConnectionError occured, retrying in {wait_time:.2f} seconds...")
                print("Traceback:")
                traceback.print_exc()
                time.sleep(wait_time)
                attempt += 1
            else:
                print("Traceback:")
                traceback.print_exc()
                return None, 0

    return None, 0


def process_with_llm(model_name, system_prompt, user_prompt):
    completion, inference_time_ms = invoke_llm(model_name, system_prompt, user_prompt)
    return completion, inference_time_ms
