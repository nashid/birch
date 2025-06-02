import csv
import os
import tiktoken

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def num_tokens_from_string_gpt_4o(string: str) -> int:
    encoding_name = "o200k_base"
    return num_tokens_from_string(string, encoding_name)


def num_tokens_from_string_gpt_4(string: str) -> int:
    encoding_name = "cl100k_base"
    return num_tokens_from_string(string, encoding_name)
