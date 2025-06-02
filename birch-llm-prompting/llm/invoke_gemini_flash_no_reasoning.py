import time
import traceback
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
def invoke_gemini(model_name,
                  system_prompt,
                  user_prompt,
                  thinking_budget=0,
                  temperature=0.0,
                  top_p=1.0,
                  max_output_tokens=4096):

    client = genai.Client(api_key=api_key)

    attempt = 0
    backoff = 60  # base backoff in seconds
    max_cumulative_backoff = 600  # total allowed backoff
    cumulative_backoff = 0

    content = f"{system_prompt}\n\n{user_prompt}"

    while True:
        try:
            start_time = time.time()
            response = client.models.generate_content(
                model=model_name,
                contents=content,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
                    temperature=temperature,
                    top_p=top_p,
                    max_output_tokens=max_output_tokens
                )
            )
            end_time = time.time()

            inference_time_ms = (end_time - start_time) * 1000
            completion = response.text
            print("Gemini response obtained")
            return completion, inference_time_ms

        except Exception as e:
            print(f"Gemini API error: {e}")
            # Exponential backoff
            wait_time = backoff * (2 ** attempt)
            cumulative_backoff += wait_time

            if cumulative_backoff >= max_cumulative_backoff:
                print("Maximum cumulative backoff time exceeded. Aborting.")
                break

            print(f"Retrying in {wait_time:.2f} seconds...")
            traceback.print_exc()
            time.sleep(wait_time)
            attempt += 1

    return None, 0


def process_with_gemini(model_name, system_prompt, user_prompt, api_key, **kwargs):
    """
    Wrapper function to invoke Gemini, mimicking the process_with_llm signature.
    """
    return invoke_gemini(model_name, system_prompt, user_prompt, api_key, **kwargs)

