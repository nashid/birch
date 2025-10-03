import os
import subprocess
import shutil

class PatchValidation:
    def __init__(self, patch_code):
        self.patch_code = patch_code

    def apply_patch(self, bug_info, buggy_file_path, encodings, bug_num, current_bug, LINUX_PATCHES_PATH, MODE):
        start_loc = bug_info["buggy_code"][str(bug_num)]['start_line']
        end_loc = bug_info["buggy_code"][str(bug_num)]['end_line']
        patch_lines = self.patch_code.strip().split('\n')
        patched_lines = []

        pre_patch_path = f"{buggy_file_path}.pre_patch"
        shutil.copy(buggy_file_path, pre_patch_path)

        orig_buggy_code = None
        encoding_used = None
        for encoding in encodings:
            try:
                with open(buggy_file_path, 'r', encoding=encoding) as file:
                    orig_buggy_code = file.readlines()
                    encoding_used = encoding
                    break
            except Exception as e:
                print(f"Error reading {buggy_file_path} with encoding {encoding}: {e}")

        with open(buggy_file_path, 'w', encoding=encoding_used, errors='ignore') as file:
            for idx, line in enumerate(orig_buggy_code):
                if idx == start_loc - 1:
                    for patch_line in patch_lines:
                        file.write(patch_line.rstrip() + '\n')
                        patched_lines.append(patch_line.rstrip())
                if idx < start_loc - 1 or idx > end_loc - 1:
                    file.write(line)

        post_patch_path = f"{buggy_file_path}.post_patch"
        shutil.copy(buggy_file_path, post_patch_path)

        if not os.path.exists(LINUX_PATCHES_PATH):
            os.makedirs(LINUX_PATCHES_PATH)
        patch_file_path = os.path.join(LINUX_PATCHES_PATH, f'{current_bug}_bug_{bug_num}_{MODE}.patch')
        with open(patch_file_path, 'w') as patch_file:
            subprocess.run(['diff', '-u', pre_patch_path, post_patch_path], stdout=patch_file)

        os.remove(pre_patch_path)
        os.remove(post_patch_path)

        return