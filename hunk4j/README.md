# Project Overview

This directory contains three main components:

1. **Patches**  
   Raw diff files (both fixed and unfixed) imported from the Hunk4J repository. Each patch represents a buggy change or its corresponding fix.

2. **AST Driven Context Extraction**  
   Java code that uses JavaParser to locate and extract the methods (and their line boundaries) in which bugs occur. This module helps identify the exact method- and class-level context around each hunk.

3. **Metadata**  
   A collection of JSON files, each containing metadata for a particular fix.

4. **Metadata Extraction**  
    Code to extract the metadata and store them in the config files in **dataset**.
