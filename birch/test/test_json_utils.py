import unittest
from unittest.mock import patch, mock_open, MagicMock
import subprocess
import requests
from bs4 import BeautifulSoup
import re
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.d4j_json_utils import get_bug_report_info, get_buggy_lines, get_failing_tests, extract_test_method_content, determine_bug_type, get_buggy_files, extract_hunks_from_file, explicit_delineation, find_enclosing_block, count_hunks_and_lines


class TestBugProcessingFunctions(unittest.TestCase):
    
    @patch('subprocess.run')
    @patch('requests.get')
    def test_get_bug_report_info(self, mock_get, mock_run):
        mock_run.return_value.stdout = "Bug report url:\nhttps://issues.apache.org/jira/browse/CLI-51\n"
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = """
            <div id='descriptionmodule'>
            Description
            If a parameter value is passed that contains a hyphen as the (delimited) first
            character, CLI parses this a parameter. For example using the call
            java myclass -t "-something"
            Results in the parser creating the invalid parameter -o (noting that it is
            skipping the 's')
            My code is using the Posix parser as follows
            Options options = buildCommandLineOptions();
            CommandLineParser parser = new PosixParser();
            CommandLine commandLine = null;
            try {
                commandLine = parser.parse(options, args);
            } catch (ParseException e) {
                System.out.println("Invalid parameters. " + e.getMessage() + NEW_LINE);
                System.exit(EXIT_CODE_ERROR);
            }
            This has been tested against the nightly build dated 20050503.
            </div>
        """
        
        url, description = get_bug_report_info('Cli', 2)
        self.assertEqual(url, 'https://issues.apache.org/jira/browse/CLI-51')
        self.assertIn('If a parameter value is passed that contains a hyphen', description)
        self.assertIn('My code is using the Posix parser as follows', description)
        
    @patch('builtins.open', new_callable=mock_open, read_data='diff --git a/source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java b/source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java\nindex 4a54655..226b25a 100644\n--- a/source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java\n+++ b/source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java\n@@ -1794,7 +1794,7 @@ public abstract class AbstractCategoryItemRenderer extends AbstractRenderer\n         }\n         int index = this.plot.getIndexOf(this);\n         CategoryDataset dataset = this.plot.getDataset(index);\n-        if (dataset == null) {\n+        if (dataset != null) {\n             return result;\n         }\n         int seriesCount = dataset.getRowCount();\n')
    def test_get_buggy_lines(self, mock_file):
        patch_file_path = '~/Desktop/defects4j/framework/projects/Chart/patches/1.src.patch'
        expected_result = {
            'source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java': [(1794, 1801)]
        }
        result = get_buggy_lines(patch_file_path)
        self.assertEqual(result, expected_result)
        
    @patch('subprocess.run')
    def test_get_failing_tests(self, mock_run):
        mock_run.return_value.stdout = " - org.apache.commons.cli.PatternOptionBuilderTest::testSimplePattern\n   --> junit.framework.AssertionFailedError: number flag n expected:<4.5> but was:<4.5>\n"
        result = get_failing_tests('Cli', 3)
        expected_result = [
            ('org.apache.commons.cli.PatternOptionBuilderTest', 'testSimplePattern', 'junit.framework.AssertionFailedError: number flag n expected:<4.5> but was:<4.5>')
        ]
        self.assertEqual(result, expected_result)
    
    def test_extract_test_method_content(self):
        test_file_path = os.path.join(os.path.dirname(__file__), 'test_resources', 'testIssue.java')
        with open(test_file_path, 'r') as file:
          test_content = file.read()

        result = extract_test_method_content(test_content, 'testIssue821')
        expected_test_code = """testIssue821() {\n    foldSame(\"var a =(Math.random()>0.5? '1' : 2 ) + 3 + 4;\");\n    foldSame(\"var a = ((Math.random() ? 0 : 1) ||\" +\n             \"(Math.random()>0.5? '1' : 2 )) + 3 + 4;\");\n  }"""
        self.assertIn(expected_test_code, result)
    
    @patch('utils.d4j_json_utils.count_hunks_and_lines')
    def test_determine_bug_type(self, mock_count):
        mock_count.return_value = (3, 18, False, 1)
        result = determine_bug_type('Cli', 18, '/Users/danielding/Desktop/defects4j')
        self.assertEqual(result, 'single_file_three_hunks')

        mock_count.return_value = (1, 7, True, 1)
        result = determine_bug_type('Chart', 1, '/Users/danielding/Desktop/defects4j')
        self.assertEqual(result, 'single_line_bug')

        # Test case for "single_hunk_3_or_more_lines"
        mock_count.return_value = (1, 7, False, 1)
        result = determine_bug_type('Chart', 3, '/Users/danielding/Desktop/defects4j')
        self.assertEqual(result, 'single_hunk_3_or_more_lines')

        # Test case for "single_file_two_hunks"
        mock_count.return_value = (2, 9, False, 1)
        result = determine_bug_type('Chart', 15, '/Users/danielding/Desktop/defects4j')
        self.assertEqual(result, 'single_file_two_hunks')

        # Test case for "single_file_four_or_more_hunks"
        mock_count.return_value = (6, 34, False, 1)
        result = determine_bug_type('Chart', 25, '/Users/danielding/Desktop/defects4j')
        self.assertEqual(result, 'single_file_four_or_more_hunks')
    
        mock_count.return_value = (2, 25, False, 2)
        result = determine_bug_type('Cli', 30, '/Users/danielding/Desktop/defects4j')
        self.assertEqual(result, 'multi_file_two_hunks')

        # Test case for "multi_file_three_hunks"
        mock_count.return_value = (3, 25, False, 3)
        result = determine_bug_type('Cli', 31, '/Users/danielding/Desktop/defects4j')
        self.assertEqual(result, 'multi_file_three_hunks')

        # Test case for "multi_file_four_or_more_hunks"
        mock_count.return_value = (7, 35, False, 4)
        result = determine_bug_type('Closure', 149, '/Users/danielding/Desktop/defects4j')
        self.assertEqual(result, 'multi_file_four_or_more_hunks')


    @patch('subprocess.run')
    def test_get_buggy_files(self, mock_run):
        mock_run.return_value.stdout = "List of modified sources\n - com.google.javascript.jscomp.TypeCheck\n"
        result = get_buggy_files('Closure', 2)
        self.assertEqual(result, ['src/com/google/javascript/jscomp/TypeCheck.java'])

    def setUp(self):
        self.localized_content = [
            "public class Test {",
            "    public void method1() {",
            "        // some code",
            "    }",
            "    public void method2() {",
            "        // buggy code",
            "        int x = 0;",
            "    }",
            "    public void method3() {",
            "        // some other code",
            "    }",
            "}"
        ]
        self.buggy_lines_list = [(4, 10)]
        self.buggy_file = "Test.java"
        self.processed_ranges = []
        self.bug_counter = 0
        self.buggy_codes = [
            {
                'start_line': 4,
                'end_line': 10,
                'file': 'Test.java',
                'code': "    public void method2() {\n        // buggy code\n        int x = 0;\n    }\n"
            }
        ]

        test_file_path = os.path.join(os.path.dirname(__file__), 'test_resources', 'Week.java')
        with open(test_file_path, 'r') as file:
          test_content = file.read()
        
        self.new_localized_content = test_content.split("\n")
        self.new_buggy_lines_list = [(172, 179)]
        self.new_buggy_file = "source/org/jfree/data/time/Week.java"
        self.new_processed_ranges = []
        self.new_bug_counter = 0
        self.new_buggy_codes = [
            {
                "start_line": 173,
                "end_line": 176,
                "file": "source/org/jfree/data/time/Week.java",
                "code": "public Week(Date time, TimeZone zone) {\n    // defer argument checking...\n    this(time, RegularTimePeriod.DEFAULT_TIME_ZONE, Locale.getDefault());\n}"
            }
        ]

    def test_extract_hunks_from_file(self):
        hunks, buggy_codes, hunk_mapping, bug_counter = extract_hunks_from_file(
            self.localized_content, self.buggy_lines_list, self.buggy_file, self.processed_ranges, self.bug_counter, self.buggy_codes, existing_buggy_codes=True
        )

        expected_hunks = [
            {
                'start_line': 7,
                'end_line': 7,
                'file': 'Test.java',
                'code': "<START_BUG>\n        int x = 0;\n<END_BUG>"
            }
        ]
        expected_hunk_mapping = {'0': expected_hunks}
        
        self.assertEqual(hunks, expected_hunks)
        self.assertEqual(hunk_mapping, expected_hunk_mapping)
        self.assertEqual(bug_counter, 1)


        hunks_1, buggy_codes_1, hunk_mapping_1, bug_counter_1 = extract_hunks_from_file(
            self.new_localized_content, self.new_buggy_lines_list, self.new_buggy_file, self.new_processed_ranges, self.new_bug_counter, self.new_buggy_codes, existing_buggy_codes=True
        )
        expected_hunks_1 = [
            {
                "start_line": 175,
                "end_line": 176,
                "file": "source/org/jfree/data/time/Week.java",
                "code": "<START_BUG>\n         this(time, RegularTimePeriod.DEFAULT_TIME_ZONE, Locale.getDefault());\n     }\n<END_BUG>"
            }
        ]
        expected_hunk_mapping_1 = {'0': expected_hunks_1}
        
        self.assertEqual(hunks_1, expected_hunks_1)
        self.assertEqual(hunk_mapping_1, expected_hunk_mapping_1)
        self.assertEqual(bug_counter_1, 1)


    def test_find_enclosing_block_with_provided_data(self):
        test_file_path = os.path.join(os.path.dirname(__file__), 'test_resources', 'CommandLine.java')
        with open(test_file_path, 'r') as file:
            localized_content = file.read()
            content = localized_content.split('\n')

        test_cases = [
            {"start_line": 19, "end_line": 24, "expected_start": 18, "expected_end": 23},
            {"start_line": 46, "end_line": 52, "expected_start": 39, "expected_end": 51},
            {"start_line": 69, "end_line": 70, "expected_start": 66, "expected_end": 69},
            {"start_line": 93, "end_line": 99, "expected_start": 88, "expected_end": 100},
            {"start_line": 149, "end_line": 159, "expected_start": 146, "expected_end": 161},
            {"start_line": 169, "end_line": 170, "expected_start": 39, "expected_end": 169},
            {"start_line": 277, "end_line": 288, "expected_start": 274, "expected_end": 287},
            {"start_line": 298, "end_line": 299, "expected_start": 295, "expected_end": 298},
            {"start_line": 308, "end_line": 309, "expected_start": 305, "expected_end": 314},
            {"start_line": 316, "end_line": 314, "expected_start": 305, "expected_end": 314},
        ]

        for case in test_cases:
            with self.subTest(case=case):
                block_start, block_end = find_enclosing_block(content, case["start_line"], case["end_line"])
                self.assertEqual((block_start, block_end), (case["expected_start"], case["expected_end"]))

    def test_explicit_delineation(self):
        buggy_codes = [
            {
                'start_line': 1,
                'end_line': 5,
                'file': 'test_file.java',
                'code': 'public void test() {\n    // buggy line 1\n    // buggy line 2\n    // buggy line 3\n    // buggy line 4\n}'
            }
        ]
        hunk_mapping = {
            '0': [
                {'start_line': 2, 'end_line': 3, 'file': 'test_file.java', 'code': '// buggy line 1\n// buggy line 2'}
            ]
        }
        expected_output = [
            {
                'start_line': 1,
                'end_line': 5,
                'file': 'test_file.java',
                'code': 'public void test() {\n<START_BUG>\n    // buggy line 1\n    // buggy line 2\n<END_BUG>\n    // buggy line 3\n    // buggy line 4\n}'
            }
        ]
        
        result = explicit_delineation(buggy_codes, hunk_mapping)
        self.assertEqual(result, expected_output)

        buggy_codes_1 = [
            {
                "start_line": 173,
                "end_line": 176,
                "file": "source/org/jfree/data/time/Week.java",
                "code": "public Week(Date time, TimeZone zone) {\n    // defer argument checking...\n    this(time, RegularTimePeriod.DEFAULT_TIME_ZONE, Locale.getDefault());\n}"
            }
        ]
        hunk_mapping_1 = {
            "0": [
                {
                    "start_line": 175,
                    "end_line": 176,
                    "file": "source/org/jfree/data/time/Week.java",
                    "code": "<START_BUG>\n        this(time, RegularTimePeriod.DEFAULT_TIME_ZONE, Locale.getDefault());\n    }\n<END_BUG>"
                }
            ]
        }
        expected_output_1 = [
            {
                "start_line": 173,
                "end_line": 176,
                "file": "source/org/jfree/data/time/Week.java",
                "code": "public Week(Date time, TimeZone zone) {\n    // defer argument checking...\n<START_BUG>\n    this(time, RegularTimePeriod.DEFAULT_TIME_ZONE, Locale.getDefault());\n}\n<END_BUG>"
            }
        ]
        result_1 = explicit_delineation(buggy_codes_1, hunk_mapping_1)
        self.assertEqual(result_1, expected_output_1)

    def test_negative_start_end_index(self):
        buggy_codes = [
            {
                'start_line': 10,
                'end_line': 20,
                'file': 'test_file.java',
                'code': 'line 10\nline 11\nline 12\nline 13\nline 14\nline 15\nline 16\nline 17\nline 18\nline 19\nline 20'
            }
        ]
        hunk_mapping = {
            '0': [
                {'start_line': 8, 'end_line': 11, 'file': 'test_file.java', 'code': 'line 8\nline 9\nline 10\nline 11'}
            ]
        }
        expected_output = [
            {
                'start_line': 10,
                'end_line': 20,
                'file': 'test_file.java',
                'code': '<START_BUG>\nline 10\nline 11\n<END_BUG>\nline 12\nline 13\nline 14\nline 15\nline 16\nline 17\nline 18\nline 19\nline 20'
            }
        ]
        
        result = explicit_delineation(buggy_codes, hunk_mapping)
        self.assertEqual(result, expected_output)

    def test_out_of_range_indices(self):
        buggy_codes = [
            {
                'start_line': 1,
                'end_line': 3,
                'file': 'test_file.java',
                'code': 'line 1\nline 2\nline 3'
            }
        ]
        hunk_mapping = {
            '0': [
                {'start_line': 2, 'end_line': 5, 'file': 'test_file.java', 'code': 'line 2\nline 3\nline 4\nline 5'}
            ]
        }
        expected_output = [
            {
                'start_line': 1,
                'end_line': 3,
                'file': 'test_file.java',
                'code': 'line 1\n<START_BUG>\nline 2\nline 3\n<END_BUG>'
            }
        ]
        
        result = explicit_delineation(buggy_codes, hunk_mapping)
        self.assertEqual(result, expected_output)

if __name__ == '__main__':
    unittest.main()
