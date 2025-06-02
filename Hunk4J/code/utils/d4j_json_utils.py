import os
import re
import argparse
import subprocess
import json
import requests
from bs4 import BeautifulSoup
import logging
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import logging
import javalang
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse

def count_hunks_and_lines(file_path):
    with open(file_path, 'r', encoding='ISO-8859-1') as file:
        content = file.readlines()
        
    diff_count = 0
    hunk_count = 0
    line_count = 0
    single_line = 0
    current_file = None
    files = set()
    hunk_lines = 0
    current_hunk_lines = 0
    in_hunk = False
    prev_line = ""
    
    for line in content:
        if line.startswith('diff --git') or line.startswith('Index:'):
            diff_count += 1
            current_file = line
            files.add(current_file) 
        elif line.startswith('@@'):
            hunk_count += 1
            if in_hunk:
                hunk_lines += current_hunk_lines
            current_hunk_lines = 0
            in_hunk = True
        elif line.startswith('-'):
            line_count += 1
            current_hunk_lines += 1
        elif line.startswith('+'):
            if prev_line.startswith('-'):
                prev_line = line
                continue
            else:
                line_count += 1
                current_hunk_lines += 1
        prev_line = line

    if in_hunk:
        hunk_lines += current_hunk_lines

    single_line = 1 if hunk_lines == 1 else 0
    multi_hunk = 1 if hunk_count > 1 else 0
    single_hunk = 1 if hunk_count == 1 and hunk_lines > 1 else 0
    
    return hunk_count, line_count, single_line, len(files)

def d4j_path_prefix(proj, bug_num):
    if proj == 'Chart':
        return 'source/'
    elif proj == 'Closure':
        return 'src/'
    elif proj == 'Lang':
        if bug_num <= 35:
            return 'src/main/java/'
        else:
            return 'src/java/'
    elif proj == 'Math':
        if bug_num <= 84:
            return 'src/main/java/'
        else:
            return 'src/java/'
    elif proj == 'Mockito':
        return 'src/'
    elif proj == 'Time':
        return 'src/main/java/'
    elif proj == 'Cli':
        if bug_num <= 29:
            return 'src/java/'
        else:
            return 'src/main/java/'
    elif proj == 'Codec':
        if bug_num <= 10:
            return 'src/java/'
        else:
            return 'src/main/java/'
    elif proj == 'Collections':
        return 'src/main/java/'
    elif proj == 'Compress':
        return 'src/main/java/'
    elif proj == 'Csv':
        return 'src/main/java/'
    elif proj == 'Gson':
        return 'gson/src/main/java/'
    elif proj in ('JacksonCore', 'JacksonDatabind', 'JacksonXml'):
        return 'src/main/java/'
    elif proj == 'Jsoup':
        return 'src/main/java/'
    elif proj == 'JxPath':
        return 'src/java/'
    else:
        raise ValueError(f'Unrecognized project {proj}')
    
def d4j_test_path_prefix(proj, bug_num):
    if proj == 'Chart':
        return 'tests/'
    elif proj == 'Closure':
        return 'test/'
    elif proj == 'Lang':
        if bug_num <= 35:
            return 'src/test/java/'
        else:
            return 'src/test/'
    elif proj == "Math":
        if bug_num <= 84:
            return 'src/test/java/'
        else:
            return 'src/test/'
    elif proj == 'Mockito':
        return 'test/'
    elif proj == "Time":
        return 'src/test/java/'
    elif proj == 'Cli':
        if bug_num <= 29:
            return 'src/test/'
        else:
            return 'src/test/java/'
    elif proj == 'Codec':
        if bug_num <= 10:
            return 'src/test/'
        else:
            return 'src/test/java/'
    elif proj == 'Collections':
        return 'src/test/java/'
    elif proj == 'Compress':
        return 'src/test/java/'
    elif proj == 'Csv':
        return 'src/test/java/'
    elif proj == 'Gson':
        return 'gson/src/test/java/'
    elif proj in ('JacksonCore', 'JacksonDatabind', 'JacksonXml'):
        return 'src/test/java/'
    elif proj == 'Jsoup':
        return 'src/test/java/'
    elif proj == 'JxPath':
        return 'src/test/'
    else:
        raise ValueError(f'Cannot find test path prefix for {proj}{bug_num}')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_url_with_playwright(url, project, bug_id, retries=2):
    for attempt in range(retries):
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                    ]
                )
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/112.0.0.0 Safari/537.36"
                    ),
                    locale="en-US",
                    java_script_enabled=True,
                    bypass_csp=True,
                    extra_http_headers={
                        "Referer": url,
                        "Accept-Language": "en-US,en;q=0.9",
                    }
                )
                context.route("**/*.{png,jpg,jpeg,svg,webp,woff,woff2,css}", lambda route: route.abort())
                page = context.new_page()
                page.set_default_navigation_timeout(30000)
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_selector("body", timeout=30000)
                content = page.content()
                browser.close()
                return content
        except Exception as e:
            logging.error(f"Playwright fetch error for {project}-{bug_id} (attempt {attempt+1}): {e}")
            if attempt == retries - 1:
                return None

def fetch_json_with_retries(url, project, bug_id, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error fetching JSON URL {url} for {project}-{bug_id} on attempt {attempt + 1}: {e}")
            if attempt == retries - 1:
                return None

def parse_bug_report_description(url, project, bug_id):
    if not url or url == "UNKNOWN":
        logging.warning(f"Bug report URL is 'UNKNOWN' for {project}-{bug_id}")
        return ""
    
    if project.lower() == 'closure' and url.endswith('.json'):
        json_data = fetch_json_with_retries(url, project, bug_id)
        if json_data and 'summary' in json_data:
            return json_data['summary']
        logging.error(f"Failed to fetch or parse JSON for {project}-{bug_id}")
        return "Error fetching or parsing JSON"
    
    parsed = urlparse(url)
    if parsed.netloc.endswith("github.com"):
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 4 and parts[2] in ("issues", "pull"):
            owner, repo, kind, number = parts[:4]
            if kind == "issues":
                api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
            else:  # pull
                api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
            headers = {"Accept": "application/vnd.github.v3+json"}
            token = os.getenv("GITHUB_TOKEN")
            if token:
                headers["Authorization"] = f"token {token}"
            try:
                r = requests.get(api_url, headers=headers, timeout=10)
                if r.ok:
                    return r.json().get("body", "").strip()
                else:
                    logging.error(f"GitHub API {r.status_code} for {project}-{bug_id} → {api_url}")
            except Exception as e:
                logging.error(f"Error fetching GitHub API for {project}-{bug_id}: {e}")

    description = ""
    page_source = fetch_url_with_playwright(url, project, bug_id)
    if page_source:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_source, "html.parser")
            selectors = [
                "div#descriptionmodule",
                "div.ticket-content",
                "div.markdown_content",
                "td.comment-body",
                "div.review-comment",
                "body",
            ]
            for sel in selectors:
                el = soup.select_one(sel)
                if el and el.get_text(strip=True):
                    description = el.get_text("\n", strip=True)
                    break
            if not description:
                description = soup.get_text("\n", strip=True)
        except Exception as e:
            logging.error(f"Error parsing HTML for {project}-{bug_id}: {e}")
            description = "Error parsing bug description"
    else:
        description = "Error fetching bug description after retries"

    return description

def get_bug_report_info(project, bug_id):
    cmd = f"defects4j info -p {project} -b {bug_id}"
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    lines = result.stdout.splitlines()
    url = ""
    for i, line in enumerate(lines):
        if line.startswith("Bug report url:"):
            url = lines[i + 1].strip()
            break
    
    description = parse_bug_report_description(url, project, bug_id)
    return url, description

def get_buggy_lines(patch_file_path):
    buggy_lines = {}
    try:
        with open(patch_file_path, 'r', encoding='utf-8') as patch_file:
            lines = patch_file.readlines()
    except UnicodeDecodeError:
        print(f"UnicodeDecodeError: Could not read {patch_file_path} due to encoding issues.")
        return buggy_lines

    current_file = None
    for line in lines:
        if line.startswith('---'):
            current_file = line.split(' ')[1].strip('a/').strip()
            java_index = current_file.find('.java')
            if java_index != -1:
                current_file = current_file[:java_index + 5]
        if line.startswith('@@'):
            match = re.search(r'\+(\d+),(\d+)', line)
            if match:
                start_line = int(match.group(1))
                line_count = int(match.group(2))
                end_line = start_line + line_count
                if current_file not in buggy_lines:
                    buggy_lines[current_file] = []
                buggy_lines[current_file].append((start_line, end_line))
    return buggy_lines

def get_failing_tests(project, bug_id):
    bug_id = int(bug_id)
    cmd = f"defects4j info -p {project} -b {bug_id}"
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout
    test_methods = []
    pattern_test = re.compile(r' - (.*)::(.*)')
    pattern_error = re.compile(r'   --> (.*)')
    for line in output.split('\n'):
        match_test = pattern_test.match(line)
        if match_test:
            current_test = (match_test.group(1), match_test.group(2))
        match_error = pattern_error.match(line)
        if match_error:
            clean_err_msg = match_error.group(1)
            if current_test:
                test_methods.append((*current_test, clean_err_msg))
                current_test = None
    return test_methods

def extract_test_method_content(test_file_content, method_name):
    start_index = test_file_content.find(f"{method_name}")
    if start_index == -1:
        return None

    start_of_method = test_file_content.find('{', start_index)
    if start_of_method == -1:
        return None

    brace_stack = []
    end_of_method = start_of_method

    while end_of_method < len(test_file_content):
        char = test_file_content[end_of_method]
        if char == '{':
            brace_stack.append(char)
        elif char == '}':
            brace_stack.pop()
            if not brace_stack:
                break  
        end_of_method += 1

    if not brace_stack:  
        return test_file_content[start_index:end_of_method + 1]
    else:
        return None 

def determine_bug_type(project, bug_id, defects4j_home):
    patch_file_path = os.path.join(defects4j_home, f'framework/projects/{project}/patches/{bug_id}.src.patch')
    hunk_count, line_count, single_line, file_count = count_hunks_and_lines(patch_file_path)
    
    if single_line:
        return 'single_line_bug'
    elif hunk_count == 1:
        if line_count == 2:
            return 'single_hunk_2_lines'
        elif line_count >= 3:
            return 'single_hunk_3_or_more_lines'
    elif hunk_count > 1:
        if hunk_count == 2 and file_count == 1:
            return 'single_file_two_hunks'
        elif hunk_count == 3 and file_count == 1:
            return 'single_file_three_hunks'
        elif hunk_count >= 4 and file_count == 1:
            return 'single_file_four_or_more_hunks'
        elif hunk_count == 2 and file_count > 1:
            return 'multi_file_two_hunks'
        elif hunk_count == 3 and file_count > 1:
            return 'multi_file_three_hunks'
        elif hunk_count >= 4 and file_count > 1:
            return 'multi_file_four_or_more_hunks'
    return 'unknown'

def get_buggy_files(proj, bug_num):
    cmd = f"defects4j info -p {proj} -b {bug_num}"
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    lines = result.stdout.splitlines()
    buggy_files = []
    capture = False
    for line in lines:
        if line.startswith('List of modified sources'):
            capture = True
            continue
        if capture:
            if line.startswith(" - "):
                modified_file = line[3:].strip().replace('.', '/') + '.java'
                prefix = d4j_path_prefix(proj, int(bug_num))
                buggy_files.append(os.path.join(prefix, modified_file))
    return buggy_files


def extract_hunks_from_file(localized_content, buggy_lines_list, buggy_file, processed_ranges, bug_counter, buggy_codes, MODE, bug_id):
    hunks = []
    hunk_mapping = {}

    for start_line, end_line in sorted(buggy_lines_list, key=lambda x: x[1]):
        content_copy = localized_content[:]
        if end_line - 3 > start_line + 2 or 0 <= start_line <= 3:
            content_copy.insert(end_line - 4, '<END_BUG>')
            end_index = end_line - 4
        else:
            content_copy.insert(start_line + 3, '<END_BUG>')
            end_index = start_line + 3
        if start_line + 2 < end_line - 3 or len(content_copy) - 3 <= end_line <= len(content_copy):
            content_copy.insert(start_line + 2, '<START_BUG>')
            start_index = start_line + 3
        else:
            content_copy.insert(end_line - 3, '<START_BUG>')
            start_index = end_line - 2

        hunk_code = '\n'.join(content_copy[start_index - 1:end_index + 2])
        hunk = {
            'start_line': start_index,
            'end_line': end_index,
            'file': buggy_file,
            'code': hunk_code
        }
        hunks.append(hunk)

        is_within_processed_range = any(
            range_start <= start_line + 3 <= range_end and range_start <= end_line - 3 <= range_end
            for range_start, range_end in processed_ranges
        )
        if is_within_processed_range:
            buggy_code_index = next(
                (index for index, code in enumerate(buggy_codes)
                 if code['start_line'] <= start_line + 3 <= code['end_line'] and code['file'] == buggy_file),
                None
            )
            hunk_mapping_key = str(buggy_code_index)
            if hunk_mapping_key not in hunk_mapping:
                hunk_mapping[hunk_mapping_key] = []
            hunk_mapping[hunk_mapping_key].append(hunk)
            continue
        
        if MODE == "block":
            block_start, block_end = find_enclosing_block(localized_content, start_line + 3, end_line - 3)
        elif MODE == "method":
            (block_start, block_end), _ = find_enclosing_method(localized_content, start_line + 3, end_line - 3, bug_id)
        if MODE == "class":
            (block_start, block_end), _ = find_enclosing_class(localized_content, start_line + 3, end_line - 3, bug_id)
        if MODE == "file":
            block_start, block_end = find_file(localized_content, start_line + 3, end_line - 3)
        if block_start == -1 or block_end == -1:
            buggy_code = '\n'.join(localized_content[start_line + 1:end_line - 2])
            buggy_code = {
                'start_line': start_line + 2,
                'end_line': end_line - 2,
                'file': buggy_file,
                'code': buggy_code
            }
        else:
            buggy_block = '\n'.join(localized_content[block_start:block_end + 1])
            buggy_code = {
                'start_line': block_start + 1,
                'end_line': block_end + 1,
                'file': buggy_file,
                'code': buggy_block.strip()
            }
        buggy_code_index = bug_counter
        buggy_codes.append(buggy_code)
        processed_ranges.append((block_start + 1, block_end + 1))
        
        hunk_mapping_key = str(buggy_code_index)
        if hunk_mapping_key not in hunk_mapping:
            hunk_mapping[hunk_mapping_key] = []
        hunk_mapping[hunk_mapping_key].append(hunk)

        bug_counter += 1

    return hunks, buggy_codes, hunk_mapping, bug_counter

def find_enclosing_block(lines, start_line, end_line):
    source_code = "\n".join(lines)
    
    tokens = list(javalang.tokenizer.tokenize(source_code))
    
    brace_stack = []
    blocks = []
    
    for token in tokens:
        if token.value == '{':
            brace_stack.append((token.position.line - 1, token.position.column))
        elif token.value == '}':
            if not brace_stack:
                continue
            open_line, open_col = brace_stack.pop()
            close_line = token.position.line - 1  
            close_col = token.position.column
            blocks.append((open_line, open_col, close_line, close_col))
    
    enclosing_blocks = [
        (open_line, open_col, close_line, close_col)
        for (open_line, open_col, close_line, close_col) in blocks
        if open_line <= start_line and close_line >= end_line
    ]
    if not enclosing_blocks:
        return start_line, end_line  
    chosen_block = None
    for block in enclosing_blocks:
        open_line, open_col, close_line, close_col = block
        if chosen_block is None:
            chosen_block = block
        else:
            if open_line > chosen_block[0] or (
               open_line == chosen_block[0] and open_col > chosen_block[1]):
                chosen_block = block
    
    start_index, open_col, end_index, close_col = chosen_block
    

    brace_token_index = None
    for i, token in enumerate(tokens):
        if token.value == '{' and token.position.line - 1 == start_index and token.position.column == open_col:
            brace_token_index = i
            break
    
    if brace_token_index is not None and brace_token_index > 0:
        prev_token = tokens[brace_token_index - 1]
        prev_token_line = prev_token.position.line - 1  
        if prev_token.value not in ['}', ';']:
            start_index = prev_token_line
    
    return (start_index, end_index)

def _lookup_in_javaparser_class(bug_name, start_line, end_line):
    with open('../redwood/config/enclosing_class_context_javaparser.json', 'r', encoding='utf-8') as f:
        _JP_INDEX = json.load(f)
    bug = _JP_INDEX.get(bug_name)
    if not bug:
        return None

    for entry in bug.get('entries', []):       
        if (str(entry['span_start']) == str(start_line) and
            str(entry['span_end'])   == str(end_line)):
            return (entry['start_line'] - 1, entry['end_line'] - 1)
    return None


def find_enclosing_class(lines,
                          start_line,
                          end_line,
                          bug_name):
    lookup = _lookup_in_javaparser_class(bug_name, start_line, end_line - 1)

    contained = False
    if lookup is not None:
        method = True
        return (lookup), contained
    
    if end_line - 2 < start_line - 1:
        end_line = start_line + 1
    return (start_line - 1, end_line - 2), contained

def _lookup_in_javaparser_method(bug_name, start_line, end_line):
    with open('../redwood/config/enclosing_method_context_javaparser.json', 'r', encoding='utf-8') as f:
        _JP_INDEX = json.load(f)
    bug = _JP_INDEX.get(bug_name)
    if not bug:
        return None

    for entry in bug.get('entries', []):       
        if (str(entry['span_start']) == str(start_line) and
            str(entry['span_end'])   == str(end_line)):
            return (entry['method_start'] - 1, entry['method_end'] - 1)
    return None


def find_enclosing_method(lines,
                          start_line,
                          end_line,
                          bug_name):
    lookup = _lookup_in_javaparser_method(bug_name, start_line, end_line - 1)

    method = False
    if lookup is not None:
        method = True
        return (lookup), method
    
    if end_line - 2 < start_line - 1:
        end_line = start_line + 1
    return (start_line - 1, end_line - 2), method

def find_file(lines, start_line, end_line):
    return (0, len(lines) - 1)

def classify_single_hunk(file_lines, start0, end0, bug_name):
    (m_start, m_end), method = find_enclosing_method(file_lines, start0, end0, bug_name)
    if method:
        return "method"

    (c_start, c_end), enclosed = find_enclosing_class(file_lines, start0, end0, bug_name)
    if enclosed:
        return "class"

    return "file"


def decide_bug_scope(hunk_scopes):
    if all(s == "method" for s in hunk_scopes):
        return "method"
    if any(s == "class" for s in hunk_scopes) and all(s in {"method", "class"} for s in hunk_scopes):
        return "class"
    return "file"


def load_existing_buggy_code(json_files, current_bug):
    current_bug = current_bug.replace('_', '-')
    for json_file in json_files:
        if os.path.exists(json_file):
            with open(json_file, 'r') as file:
                data = json.load(file)
                if current_bug in data:
                    bug_data = data[current_bug]
                    if 'buggy' in bug_data:
                        return [{
                            'start_line': bug_data['start'],
                            'end_line': bug_data['end'],
                            'file': bug_data['loc'],
                            'code': bug_data['buggy']
                        }]
                    elif 'functions' in bug_data:
                        return [{
                            'start_line': func['start_loc'],
                            'end_line': func['end_loc'],
                            'file': func['path'],
                            'code': func['buggy_function']
                        } for func in bug_data['functions']]
    return None

def explicit_delineation(buggy_codes, hunk_mapping):
    delineated_codes = []
    for key, hunks in hunk_mapping.items():
        buggy_code_entry = buggy_codes[int(key)]
        buggy_code_lines = buggy_code_entry['code'].split('\n')
        
        for hunk in hunks:
            start_line_index = hunk['start_line'] - buggy_code_entry['start_line']
            end_line_index = hunk['end_line'] - buggy_code_entry['start_line']
            if start_line_index < 0:
                start_line_index = 0
            if start_line_index >= len(buggy_code_lines):
                start_line_index = len(buggy_code_lines) - 1

            if end_line_index < 0:
                end_line_index = 0
            if end_line_index >= len(buggy_code_lines):
                end_line_index = len(buggy_code_lines) - 1
            buggy_code_lines[start_line_index] = '<START_BUG>\n' + buggy_code_lines[start_line_index]
            buggy_code_lines[end_line_index] = buggy_code_lines[end_line_index] + '\n<END_BUG>'
        
        delineated_code_entry = buggy_code_entry.copy()
        delineated_code_entry['code'] = '\n'.join(buggy_code_lines)
        delineated_codes.append(delineated_code_entry)
    
    return delineated_codes

