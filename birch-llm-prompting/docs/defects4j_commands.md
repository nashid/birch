# Defects4j Commands

## Setup 
Steps to set up Defects4J:
1. Clone Defects4J:
    - `git clone https://github.com/rjust/defects4j`

2. Initialize Defects4J (download the project repositories and external libraries, which are not included in the git repository for size purposes and to avoid redundancies):
    - `cd defects4j`
    - `cpanm --installdeps .`
    - `./init.sh`

3. Add Defects4J's executables to your PATH:
    - `export PATH=$PATH:"path2defects4j"/framework/bin`
    ("path2defects4j" points to the directory to which you cloned Defects4J; it
     looks like "/user/yourComputerUserName/desktop/defects4j".)

4. Check installation:
    - `defects4j info -p Lang`

## Description
Relevant commands regarding operations of defects4j.

## Reproduction of bugs
To reproduce each bugs, use the following commands:
   - `defects4j checkout -p <project_name> -v <bug_id>b -w <path-to-working-directory>`
   - `defects4j compile -w <path-to-working-directory>`
   - `defects4j test -w <path-to-working-directory>`
   
The results should look like this:

   `Processing Cli-1`<br>
   `Check out program version: Cli-1b.......................................... OK`<br>
   `Running ant (compile)...................................................... OK`<br>
   `Running ant (compile.tests)................................................ OK`<br>
   `Running ant (compile.tests)................................................ OK`<br>
   `Running ant (run.dev.tests)................................................ OK`<br>
   `Failing tests: 1`<br>
   `- org.apache.commons.cli.bug.BugCLI13Test::testCLI13`


## Finding Buggy Files
To find the buggy files, use the following command:
   - `defects4j info -p <project_name> -b <bug_id>`
The results will be:

```sh
   Determine revision date.................................................... OK
   Summary of configuration for Project: Lang
   --------------------------------------------------------------------------------
      Script dir: /Users/danielding/Desktop/defects4j/framework
         Base dir: /Users/danielding/Desktop/defects4j
      Major root: /Users/danielding/Desktop/defects4j/major
         Repo dir: /Users/danielding/Desktop/defects4j/project_repos
   --------------------------------------------------------------------------------
      Project ID: Lang
         Program: commons-lang
      Build file: /Users/danielding/Desktop/defects4j/framework/projects/Lang/Lang.build.xml
   --------------------------------------------------------------------------------
            Vcs: Vcs::Git
      Repository: /Users/danielding/Desktop/defects4j/project_repos/commons-lang.git
      Commit db: /Users/danielding/Desktop/defects4j/framework/projects/Lang/active-bugs.csv
   Number of bugs: 64
   --------------------------------------------------------------------------------

   Summary for Bug: Lang-1
   --------------------------------------------------------------------------------
   Revision ID (fixed version):
   687b2e62b7c6e81cd9d5c872b7fa9cc8fd3f1509
   --------------------------------------------------------------------------------
   Revision date (fixed version):
   2013-07-26 01:03:52 +0000
   --------------------------------------------------------------------------------
   Bug report id:
   LANG-747
   --------------------------------------------------------------------------------
   Bug report url:
   https://issues.apache.org/jira/browse/LANG-747
   --------------------------------------------------------------------------------
   Root cause in triggering tests:
   - org.apache.commons.lang3.math.NumberUtilsTest::TestLang747
      --> java.lang.NumberFormatException: For input string: "80000000"
   --------------------------------------------------------------------------------
   List of modified sources:
   - org.apache.commons.lang3.math.NumberUtils
   --------------------------------------------------------------------------------
```


   The buggy file is listed under **List of modified sources:**
   The information there is the path to directory from `src/main/` of the working directory of this version of this bug.

## Other Commands
### env
- `defects4j env`<br>
- Print the environment of defects4j executions

Output:
```sh
   --------------------------------------------------------------------------------
                        Defects4j Execution Environment 
   --------------------------------------------------------------------------------
   PWD.........................../Users/.../.../
   SHELL........................./bin/bash
   TZ............................America/Los_Angeles
   JAVA_HOME...................../Library/Java/JavaVirtualMachines/temurin-8.jdk/Contents/Home
   Java Exec...................../Library/Java/JavaVirtualMachines/temurin-8.jdk/Contents/Home/bin/java
   Java Exec Resolved............/Library/Java/JavaVirtualMachines/temurin-8.jdk/Contents/Home/bin/java
   Java Version:
   openjdk version "1.8.0_412"
   OpenJDK Runtime Environment (Temurin)(build 1.8.0_412-b08)
   OpenJDK 64-Bit Server VM (Temurin)(build 25.412-b08, mixed mode)
   Git version...................git version 2.43.0
   SVN version...................1.14.3
   Perl version..................v5.38.2
   --------------------------------------------------------------------------------
```

### mutation
- `defects4j mutation [-w work_dir] [-r | [-t single_test] [-s test_suite]] [-i instrument_classes] [-e exclude_file] [-m mutation_operators_file]`

Run mutation analysis on a buggy or a fixed project version

Output:
```sh
   Compiling mutant definition (mml).......................................... OK
   Running ant (mutate)....................................................... OK
   Running ant (compile.tests)................................................ OK
   Running ant (mutation.test)................................................ FAIL
   Executed command:  cd /Users/danielding/WORK_DIR/Lang_1 && /Users/danielding/Desktop/defects4j/major/bin/ant -f /Users/danielding/Desktop/defects4j/framework/projects/defects4j.build.xml -Dd4j.home=/Users/danielding/Desktop/defects4j -Dd4j.dir.projects=/Users/danielding/Desktop/defects4j/framework/projects -Dbasedir=/Users/danielding/WORK_DIR/Lang_1 -Dbuild.compiler=major.ant.MajorCompiler -Dmajor.kill.log=/Users/danielding/WORK_DIR/Lang_1/kill.csv  -logfile /Users/danielding/WORK_DIR/Lang_1/.mutation.log   mutation.test 2>&1
   OpenJDK 64-Bit Server VM warning: ignoring option MaxPermSize=1G; support was removed in 8.0
   Buildfile: /Users/danielding/Desktop/defects4j/framework/projects/defects4j.build.xml

   init:
      [echo] -------- commons-lang3 3.2-SNAPSHOT --------

   compile:

   compile.tests:

   update.all.tests:

   mutation.test:
      [echo] Running mutation analysis ...
      [junit] MAJOR: Mutation analysis enabled
      [junit] MAJOR: org.apache.commons.lang3.math.NumberUtilsTest[TestLang747] failed!
      [junit] MAJOR:  -> java.lang.NumberFormatException
      [junit] MAJOR:  -> "For input string: "80000000""

   BUILD FAILED
   /Users/danielding/Desktop/defects4j/framework/projects/defects4j.build.xml:225: Test org.apache.commons.lang3.math.NumberUtilsTest failed

   Total time: 5 seconds
   ---------------------------------------------------------------------------
   Mutation analysis failed on a buggy program version!
   You may need to exclude failing tests from the analysis, e.g., by setting
   the 'haltonfailure' flag to false in 'defects4j.build.xml'.
   (If this failure is unexpected, please file a bug report.)
```
### Coverage
- `defects4j coverage [-w work_dir] [-r | [-t single_test] [-s test_suite]] [-i instrument_classes]`

- Run code coverage analysis on a buggy or a fixed project version

Output:
```sh
   Running ant (compile.tests)................................................ OK
   Running ant (coverage.instrument).......................................... OK
   Running ant (run.dev.tests)................................................ OK
   Running ant (coverage.report).............................................. OK
         Lines total: 374
      Lines covered: 367
   Conditions total: 338
   Conditions covered: 295
      Line coverage: 98.1%
   Condition coverage: 87.3%
   WARNING: Some tests failed (see /Users/danielding/WORK_DIR/Lang_1/failing_tests)!
```
### bids
- `defects4j bids -p project_id`

- Print the list of active or deprecated bug IDs for a specific project

Output:
```sh
   1
   2
   3
   ...
   64
   65
```
### pids
- `defects4j pids`

- Print a list of available project IDs

- Output:
```sh
   Chart
   Cli
   Closure
   Codec
   Collections
   Compress
   Csv
   Gson
   JacksonCore
   JacksonDatabind
   JacksonXml
   Jsoup
   JxPath
   Lang
   Math
   Mockito
   Time
```
### export
- `defects4j export -p property_name [-o output_file] [-w work_dir]`

- Export version-specific properties such as classpaths, directories, or lists of tests

- Output:
```sh
   Running ant (export.tests.all)............................................. OK
```

### query
- `d4j-query -p pid [-q query] [-o output_file] [-H] [-D|-A]`

```sh
   -H
   List the available fields.

   -D
   Include only deprecated bugs. By default, only active bugs are queried. Cannot be used in conjunction with "all bugs" (-A).

   -A
   Include both active and deprecated bugs. By default, only active bugs are queried. Cannot be used in conjunction with "only deprecated bugs" (-D).
```

- Query the metadata to generate a CSV file of requested information for a specific project

Output: BugIDs dependent on query input.
