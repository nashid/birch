# Project Overview

This directory contains three main components:

1. **patches**  
   Raw diff files (both fixed and unfixed) imported from the Hunk4J repository. Each patch represents a buggy change or its corresponding fix.

2. **javaparser/**  
   Java code that uses JavaParser to locate and extract the methods (and their line boundaries) in which bugs occur. This module helps identify the exact method- and class-level context around each hunk.

3. **dataset**  
   A collection of JSON files, each containing metadata for a particular fix.

4. **code**  
    Code to extract the metadata and store them in the config files in **dataset**.
