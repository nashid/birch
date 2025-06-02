import unittest

from utils.d4j_json_utils import find_enclosing_block, find_enclosing_method, find_enclosing_class, find_file

class TestEnclosingFunctions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        We'll reuse a single code snippet containing a class, a method, 
        and an if-block for testing.
        Lines are 0-indexed. We'll map them for clarity:
         0: public class Example {
         1:     public void sayHello() {
         2:         int x = 0;
         3:         if (x == 0) {
         4:             System.out.println("Hello!");
         5:         }
         6:     }
         7: }
        """
        cls.lines = [
            "public class Example {",
            "    public void sayHello() {",
            "        int x = 0;",
            "        if (x == 0) {",
            "            System.out.println(\"Hello!\");",
            "        }",
            "    }",
            "}"
        ]
        # For reference:
        # line 0 -> "public class Example {"
        # line 1 -> "    public void sayHello() {"
        # line 2 -> "        int x = 0;"
        # line 3 -> "        if (x == 0) {"
        # line 4 -> "            System.out.println(\"Hello!\");"
        # line 5 -> "        }"
        # line 6 -> "    }"
        # line 7 -> "}"

    def test_enclosing_block_if_body(self):
        """
        Grab lines 4 to 4, inside the if block:
        if (x == 0) {
            System.out.println("Hello!");
        }
        The smallest brace-enclosed block that covers line 4 is the if statement block, 
        from line 3 to line 5 or so. 
        Let's see if it includes line 3 or line 2, etc.
        """
        start_line, end_line = 4, 4  # "System.out.println("Hello!");"
        block_start, block_end = find_enclosing_block(self.lines, start_line, end_line)
        self.assertEqual(block_start, 3)
        self.assertEqual(block_end, 5)

    def test_enclosing_block_entire_method(self):
        """
        If we select lines 2..5, that includes if-block but also the line above it.
        The if-block encloses 3..5, but line 2 isn't inside it. 
        The next bigger block is the method's braces from line 1..6.
        """
        start_line, end_line = 2, 5
        block_start, block_end = find_enclosing_block(self.lines, start_line, end_line)
        # We expect it to find the method braces from line 1..6
        # or possibly line 1..6 including the preceding line for the signature. 
        self.assertEqual(block_start, 1)  
        self.assertEqual(block_end, 6)

    def test_enclosing_class_simple(self):
        """
        If we pick lines 2..2, that's 'int x = 0;'. 
        The entire snippet is in 'Example' class from line 0..7. 
        We expect find_enclosing_class to pick the smaller of multiple classes if nested, 
        but we only have one class, so it should return 0..7
        """
        start_line, end_line = 2, 2
        c_start, c_end = find_enclosing_class(self.lines, start_line, end_line)
        self.assertEqual((c_start, c_end), (0, 7))

    def test_file_entire(self):
        """
        find_file should always return (0, len(lines)-1).
        """
        start_line, end_line = 2, 4
        f_start, f_end = find_file(self.lines, start_line, end_line)
        self.assertEqual(f_start, 0)
        self.assertEqual(f_end, len(self.lines) - 1)
    def test_enclosing_class_multiple(self):
        """
        Test file with multiple classes in the same Java source.
        We verify that find_enclosing_class picks the correct one.
        
         0: public class Alpha {
         1:     int x;
         2: }
         3: class Beta {
         4:     void doSomething() {
         5:         int y = 10;
         6:     }
         7: }
         8: class Gamma {
         9:     // empty class
         10: }
        """
        lines_multi = [
            "public class Alpha {",
            "    int x;",
            "}",
            "class Beta {",
            "    void doSomething() {",
            "        int y = 10;",
            "    }",
            "}",
            "class Gamma {",
            "    // empty class",
            "}"
        ]

        # Suppose we pick line 5 (0-based) => 'int y = 10;'
        # We expect find_enclosing_class(...) to return (3, 7), 
        # because 'Beta' starts at line 3 and ends at line 7.
        start_line, end_line = 5, 5
        c_start, c_end = find_enclosing_class(lines_multi, start_line, end_line)
        self.assertEqual(c_start, 3)
        self.assertEqual(c_end, 7)

        # Another scenario: lines 1..1 are inside 'Alpha'
        # 'Alpha' starts at line 0 and ends at line 2
        c_start2, c_end2 = find_enclosing_class(lines_multi, 1, 1)
        self.assertEqual((c_start2, c_end2), (0, 2))

        # If we pick a line in 'Gamma' (e.g. line 9), it should return (8, 10)
        c_start3, c_end3 = find_enclosing_class(lines_multi, 9, 9)
        self.assertEqual((c_start3, c_end3), (8, 10))

if __name__ == "__main__":
    unittest.main()