import unittest
from unittest.mock import patch, mock_open
import os
from jinja2 import Template
import toml
import json

def load_prompts_from_toml(toml_file_path):
    with open(toml_file_path, 'r', encoding='utf-8') as file:
        return toml.load(file)
    
def generate_prompt_mixtral(buggy_code, delineated_bug, bug_description, test_info_str, prompt_type):
    toml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'prompt_configurations', 'mixtral_prompts.toml')
    toml_path = os.path.abspath(toml_path)

    prompts = load_prompts_from_toml(toml_path)
    prompt_key = f'prompt{prompt_type}'
    
    if prompt_key not in prompts:
        raise ValueError(f"Invalid prompt type: {prompt_type}")

    template_str = prompts[prompt_key]['template']
    template = Template(template_str)
    
    context = {
        'buggy_code': buggy_code,
        'delineated_bug': delineated_bug,
        'bug_description': bug_description,
        'test_info_str': test_info_str
    }

    return template.render(context)

def generate_prompt_gpt(buggy_code, delineated_bug, bug_description, test_info_str, prompt_type):
    toml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'prompt_configurations', 'gpt_prompts.toml')
    toml_path = os.path.abspath(toml_path)
    
    prompts = load_prompts_from_toml(toml_path)
    prompt_key = f'prompt{prompt_type}'
    
    if prompt_key not in prompts:
        raise ValueError(f"Invalid prompt type: {prompt_type}")

    template_str = prompts[prompt_key]['template']
    template = Template(template_str)
    
    context = {
        'buggy_code': buggy_code,
        'delineated_bug': delineated_bug,
        'bug_description': bug_description,
        'test_info_str': test_info_str
    }

    return template.render(context)

class TestGeneratePrompts(unittest.TestCase):
    
    def setUp(self):
        self.buggy_code = "public void buggyMethod() { /* buggy code */ }"
        self.delineated_bug = "<START_BUG> public void buggyMethod() { /* buggy code */ } <END_BUG>"
        self.bug_description = "This method fails because it doesn't handle null values."
        self.test_info_str = "Here is test code 1:\n@Test\npublic void testBug() { /* test code */ }\nAnd its error message:\nNullPointerException"
        
        self.expected_prompt_mixtral_mode_4 = """
[INST] Please generate a fix for me of this bug. Below are the relevant information you will need.
Here is the buggy code with marked position of the bug inside the code block.
<START_BUG> public void buggyMethod() { /* buggy code */ } <END_BUG>
Please note that <START_BUG> indicates the beginning of the buggy lines, and <END_BUG> indicates the ending of the buggy lines.
Here is the description of the bug:
This method fails because it doesn't handle null values.
Here is test code 1:
@Test
public void testBug() { /* test code */ }
And its error message:
NullPointerException
Fix the bug in the bug code and only return the corrected code, with no comments. Do not provide anything other than the code. [/INST]
"""

        self.expected_prompt_gpt_mode_4 = """
Here is the buggy code with marked position of the bug inside the code block.
<START_BUG> public void buggyMethod() { /* buggy code */ } <END_BUG>
Please note that <START_BUG> indicates the beginning of the buggy lines, and <END_BUG> indicates the ending of the buggy lines.
Here is the description of the bug:
This method fails because it doesn't handle null values.
Here is test code 1:
@Test
public void testBug() { /* test code */ }
And its error message:
NullPointerException
Please fix the bug in this code. Only return the corrected code. Do not provide comments, explanations, or any additional text. Return only the corrected code.
"""

        self.expected_prompt_mixtral_mode_1 = """
[INST] Please generate a fix for me of this bug. Below are the relevant information you will need.
Here is the buggy code:
public void buggyMethod() { /* buggy code */ },
Fix the bug in the bug code and only return the corrected code, with no comments. Do not provide anything other than the code. [/INST]
"""

        self.expected_prompt_gpt_mode_1 = """
Here is the buggy code:
public void buggyMethod() { /* buggy code */ },
Please fix the bug in this code. Only return the corrected code. Do not provide comments, explanations, or any additional text. Return only the corrected code.
"""

        json_file_path = os.path.join(os.path.dirname(__file__),'test_resources', 'Chart_8.json')
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        
        chart_8_data = data['Chart_8']

        self.buggy_code_1 = chart_8_data['buggy_code']['0']['code']
        self.delineated_bug_1 = chart_8_data['delineated_bug']['0']['code']
        self.bug_description_1 = chart_8_data['bug_report']['bug_description']
        
        test_info = chart_8_data['triggered_tests']['0']
        self.test_info_str_1 = f"This code is buggy because of the following 1 test case failure. Test code and corresponding error messages will be shown below.\nHere is test code 1:\n{test_info['test_code']}\nand its corresponding error message:\n{test_info['clean_err_msg']}\n"

        json_file_path = os.path.join(os.path.dirname(__file__),'test_resources', 'Closure_14.json')
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        
        closure_14_data = data['Closure_14']

        self.buggy_code_2 = closure_14_data['buggy_code']['0']['code']
        self.delineated_bug_2 = closure_14_data['delineated_bug']['0']['code']
        self.bug_description_2 = closure_14_data['bug_report']['bug_description']
        
        test_info_1 = closure_14_data['triggered_tests']['0']
        test_info_2 = closure_14_data['triggered_tests']['1']
        test_info_3 = closure_14_data['triggered_tests']['2']
        self.test_info_str_2 = f"This code is buggy because of the following 1 test case failure. Test code and corresponding error messages will be shown below.\nHere is test code 1:\n{test_info_1['test_code']}\nand its corresponding error message:\n{test_info_1['clean_err_msg']}\nHere is test code 2:\n{test_info_2['test_code']}\nand its corresponding error message:\n{test_info_2['clean_err_msg']}\nHere is test code 3:\n{test_info_3['test_code']}\nand its corresponding error message:\n{test_info_3['clean_err_msg']}\n"
        
        self.expected_prompt_mixtral_mode_4_1 = """
[INST] Please generate a fix for me of this bug. Below are the relevant information you will need.
Here is the buggy code with marked position of the bug inside the code block.
public Week(Date time, TimeZone zone) {
    // defer argument checking...
<START_BUG>
    this(time, RegularTimePeriod.DEFAULT_TIME_ZONE, Locale.getDefault());
}
<END_BUG>
Please note that <START_BUG> indicates the beginning of the buggy lines, and <END_BUG> indicates the ending of the buggy lines.
Here is the description of the bug:

This code is buggy because of the following 1 test case failure. Test code and corresponding error messages will be shown below.
Here is test code 1:
testConstructor() {
        Locale savedLocale = Locale.getDefault();
        TimeZone savedZone = TimeZone.getDefault();
        Locale.setDefault(new Locale("da", "DK"));
        TimeZone.setDefault(TimeZone.getTimeZone("Europe/Copenhagen"));
        GregorianCalendar cal = (GregorianCalendar) Calendar.getInstance(
                TimeZone.getDefault(), Locale.getDefault());

        // first day of week is monday
        assertEquals(Calendar.MONDAY, cal.getFirstDayOfWeek());
        cal.set(2007, Calendar.AUGUST, 26, 1, 0, 0);
        cal.set(Calendar.MILLISECOND, 0);
        Date t = cal.getTime();
        Week w = new Week(t, TimeZone.getTimeZone("Europe/Copenhagen"));
        assertEquals(34, w.getWeek());

        Locale.setDefault(Locale.US);
        TimeZone.setDefault(TimeZone.getTimeZone("US/Detroit"));
        cal = (GregorianCalendar) Calendar.getInstance(TimeZone.getDefault());
        // first day of week is Sunday
        assertEquals(Calendar.SUNDAY, cal.getFirstDayOfWeek());
        cal.set(2007, Calendar.AUGUST, 26, 1, 0, 0);
        cal.set(Calendar.MILLISECOND, 0);

        t = cal.getTime();
        w = new Week(t, TimeZone.getTimeZone("Europe/Copenhagen"));
        assertEquals(35, w.getWeek());
        w = new Week(t, TimeZone.getTimeZone("Europe/Copenhagen"),
                new Locale("da", "DK"));
        assertEquals(34, w.getWeek());

        Locale.setDefault(savedLocale);
        TimeZone.setDefault(savedZone);
    }
and its corresponding error message:
junit.framework.AssertionFailedError: expected:<35> but was:<34>

Fix the bug in the bug code and only return the corrected code, with no comments. Do not provide anything other than the code. [/INST]
"""

        self.expected_prompt_gpt_mode_4_1 = """
Here is the buggy code with marked position of the bug inside the code block.
public Week(Date time, TimeZone zone) {
    // defer argument checking...
<START_BUG>
    this(time, RegularTimePeriod.DEFAULT_TIME_ZONE, Locale.getDefault());
}
<END_BUG>
Please note that <START_BUG> indicates the beginning of the buggy lines, and <END_BUG> indicates the ending of the buggy lines.
Here is the description of the bug:

This code is buggy because of the following 1 test case failure. Test code and corresponding error messages will be shown below.
Here is test code 1:
testConstructor() {
        Locale savedLocale = Locale.getDefault();
        TimeZone savedZone = TimeZone.getDefault();
        Locale.setDefault(new Locale("da", "DK"));
        TimeZone.setDefault(TimeZone.getTimeZone("Europe/Copenhagen"));
        GregorianCalendar cal = (GregorianCalendar) Calendar.getInstance(
                TimeZone.getDefault(), Locale.getDefault());

        // first day of week is monday
        assertEquals(Calendar.MONDAY, cal.getFirstDayOfWeek());
        cal.set(2007, Calendar.AUGUST, 26, 1, 0, 0);
        cal.set(Calendar.MILLISECOND, 0);
        Date t = cal.getTime();
        Week w = new Week(t, TimeZone.getTimeZone("Europe/Copenhagen"));
        assertEquals(34, w.getWeek());

        Locale.setDefault(Locale.US);
        TimeZone.setDefault(TimeZone.getTimeZone("US/Detroit"));
        cal = (GregorianCalendar) Calendar.getInstance(TimeZone.getDefault());
        // first day of week is Sunday
        assertEquals(Calendar.SUNDAY, cal.getFirstDayOfWeek());
        cal.set(2007, Calendar.AUGUST, 26, 1, 0, 0);
        cal.set(Calendar.MILLISECOND, 0);

        t = cal.getTime();
        w = new Week(t, TimeZone.getTimeZone("Europe/Copenhagen"));
        assertEquals(35, w.getWeek());
        w = new Week(t, TimeZone.getTimeZone("Europe/Copenhagen"),
                new Locale("da", "DK"));
        assertEquals(34, w.getWeek());

        Locale.setDefault(savedLocale);
        TimeZone.setDefault(savedZone);
    }
and its corresponding error message:
junit.framework.AssertionFailedError: expected:<35> but was:<34>

Please fix the bug in this code. Only return the corrected code. Do not provide comments, explanations, or any additional text. Return only the corrected code.
"""
        file_path = os.path.join(os.path.dirname(__file__),'test_resources', 'mixtral_closure_14.txt')
        with open(file_path, 'r') as file:
            data = file.read()
        self.expected_prompt_mixtral_mode_4_2 = data

        file_path = os.path.join(os.path.dirname(__file__),'test_resources', 'gpt_closure_14.txt')
        with open(file_path, 'r') as file:
            data = file.read()
        self.expected_prompt_gpt_mode_4_2 = data

        self.expected_prompt_mixtral_mode_1_1 = """
[INST] Please generate a fix for me of this bug. Below are the relevant information you will need.
Here is the buggy code:
public Week(Date time, TimeZone zone) {
    // defer argument checking...
    this(time, RegularTimePeriod.DEFAULT_TIME_ZONE, Locale.getDefault());
},
Fix the bug in the bug code and only return the corrected code, with no comments. Do not provide anything other than the code. [/INST]
"""

        self.expected_prompt_gpt_mode_1_1 = """
Here is the buggy code:
public Week(Date time, TimeZone zone) {
    // defer argument checking...
    this(time, RegularTimePeriod.DEFAULT_TIME_ZONE, Locale.getDefault());
},
Please fix the bug in this code. Only return the corrected code. Do not provide comments, explanations, or any additional text. Return only the corrected code.
"""
    @patch('builtins.open', new_callable=mock_open, read_data='''
[prompt1]
template = """
[INST] Please generate a fix for me of this bug. Below are the relevant information you will need.
Here is the buggy code:
{{ buggy_code }},
Fix the bug in the bug code and only return the corrected code, with no comments. Do not provide anything other than the code. [/INST]
"""

[prompt2]
template = """
[INST] Please generate a fix for me of this bug. Below are the relevant information you will need.
Here is the buggy code with marked position of the bug inside the code block.
{{ delineated_bug }}
Please note that <START_BUG> indicates the beginning of the buggy lines, and <END_BUG> indicates the ending of the buggy lines.
Fix the bug in the bug code and only return the corrected code, with no comments. Do not provide anything other than the code. [/INST]
"""

[prompt3]
template = """
[INST] Please generate a fix for me of this bug. Below are the relevant information you will need.
Here is the buggy code with marked position of the bug inside the code block.
{{ delineated_bug }}
Please note that <START_BUG> indicates the beginning of the buggy lines, and <END_BUG> indicates the ending of the buggy lines.
Here is the description of the bug:
{{ bug_description }}
Fix the bug in the bug code and only return the corrected code, with no comments. Do not provide anything other than the code. [/INST]
"""

[prompt4]
template = """
[INST] Please generate a fix for me of this bug. Below are the relevant information you will need.
Here is the buggy code with marked position of the bug inside the code block.
{{ delineated_bug }}
Please note that <START_BUG> indicates the beginning of the buggy lines, and <END_BUG> indicates the ending of the buggy lines.
Here is the description of the bug:
{{ bug_description }}
{{ test_info_str }}
Fix the bug in the bug code and only return the corrected code, with no comments. Do not provide anything other than the code. [/INST]
"""
''')
    def test_generate_prompt_mixtral(self, mock_file):
        result_mode_4 = generate_prompt_mixtral(
            self.buggy_code,
            self.delineated_bug,
            self.bug_description,
            self.test_info_str,
            4
        )
        self.assertEqual(result_mode_4.strip(), self.expected_prompt_mixtral_mode_4.strip())

        result_mode_4_1 = generate_prompt_mixtral(
            self.buggy_code_1,
            self.delineated_bug_1,
            self.bug_description_1,
            self.test_info_str_1,
            4
        )
        self.assertEqual(result_mode_4_1.strip(), self.expected_prompt_mixtral_mode_4_1.strip())

        result_mode_4_2 = generate_prompt_mixtral(
            self.buggy_code_2,
            self.delineated_bug_2,
            self.bug_description_2,
            self.test_info_str_2,
            4
        )
        self.assertEqual(result_mode_4_2.strip(), self.expected_prompt_mixtral_mode_4_2.strip())

        result_mode_1 = generate_prompt_mixtral(
            self.buggy_code,
            "",
            "",
            "",
            1
        )
        self.assertEqual(result_mode_1.strip(), self.expected_prompt_mixtral_mode_1.strip())

        result_mode_1_1 = generate_prompt_mixtral(
            self.buggy_code_1,
            "",
            "",
            "",
            1
        )
        self.assertEqual(result_mode_1_1.strip(), self.expected_prompt_mixtral_mode_1_1.strip())

    @patch('builtins.open', new_callable=mock_open, read_data='''
[prompt1]
template = """
Here is the buggy code:
{{ buggy_code }},
Please fix the bug in this code. Only return the corrected code. Do not provide comments, explanations, or any additional text. Return only the corrected code.
"""

[prompt2]
template = """
Here is the buggy code with marked position of the bug inside the code block.
{{ delineated_bug }}
Please note that <START_BUG> indicates the beginning of the buggy lines, and <END_BUG> indicates the ending of the buggy lines.
Please fix the bug in this code. Only return the corrected code. Do not provide comments, explanations, or any additional text. Return only the corrected code.
"""

[prompt3]
template = """
Here is the buggy code with marked position of the bug inside the code block.
{{ delineated_bug }}
Please note that <START_BUG> indicates the beginning of the buggy lines, and <END_BUG> indicates the ending of the buggy lines.
Here is the description of the bug:
{{ bug_description }}
Please fix the bug in this code. Only return the corrected code. Do not provide comments, explanations, or any additional text. Return only the corrected code.
"""

[prompt4]
template = """
Here is the buggy code with marked position of the bug inside the code block.
{{ delineated_bug }}
Please note that <START_BUG> indicates the beginning of the buggy lines, and <END_BUG> indicates the ending of the buggy lines.
Here is the description of the bug:
{{ bug_description }}
{{ test_info_str }}
Please fix the bug in this code. Only return the corrected code. Do not provide comments, explanations, or any additional text. Return only the corrected code.
"""
''')
    def test_generate_prompt_gpt(self, mock_file):
        result_mode_4 = generate_prompt_gpt(
            self.buggy_code,
            self.delineated_bug,
            self.bug_description,
            self.test_info_str,
            4
        )
        self.assertEqual(result_mode_4.strip(), self.expected_prompt_gpt_mode_4.strip())

        result_mode_4_1 = generate_prompt_gpt(
            self.buggy_code_1,
            self.delineated_bug_1,
            self.bug_description_1,
            self.test_info_str_1,
            4
        )
        self.assertEqual(result_mode_4_1.strip(), self.expected_prompt_gpt_mode_4_1.strip())

        result_mode_4_2 = generate_prompt_gpt(
            self.buggy_code_2,
            self.delineated_bug_2,
            self.bug_description_2,
            self.test_info_str_2,
            4
        )
        self.assertEqual(result_mode_4_2.strip(), self.expected_prompt_gpt_mode_4_2.strip())

        result_mode_1 = generate_prompt_gpt(
            self.buggy_code,
            "",
            "",
            "",
            1
        )
        self.assertEqual(result_mode_1.strip(), self.expected_prompt_gpt_mode_1.strip())

        result_mode_1_1 = generate_prompt_gpt(
            self.buggy_code_1,
            "",
            "",
            "",
            1
        )
        self.assertEqual(result_mode_1_1.strip(), self.expected_prompt_gpt_mode_1_1.strip())

if __name__ == '__main__':
    unittest.main()
