# Bug Characterization of Defects4j Bugs

| Project            | Number of Active Bugs | Single-line Bugs | Single-hunk Bugs (2 lines) | Single-hunk Bugs (>=3 lines) | Multi-hunk Bugs (1 file) | Multi-hunk Bugs (2 files) | Multi-hunk Bugs (>=3 files) |
|--------------------|-----------------------|------------------|----------------------------|------------------------------|--------------------------|---------------------------|-----------------------------|
| Chart              | 26                    | 9                | 0                          | 7                            | 8                        | 2                         | 0                           |
| Cli                | 39                    | 6                | 0                          | 16                           | 10                       | 3                         | 4                           |
| Closure            | 174                   | 26               | 0                          | 66                           | 45                       | 27                        | 10                          |
| Codec              | 18                    | 9                | 0                          | 2                            | 3                        | 1                         | 3                           |
| Collections        | 4                     | 1                | 0                          | 2                            | 1                        | 0                         | 0                           |
| Compress           | 47                    | 5                | 0                          | 24                           | 14                       | 2                         | 2                           |
| Csv                | 16                    | 5                | 0                          | 7                            | 3                        | 1                         | 0                           |
| Gson               | 18                    | 4                | 0                          | 7                            | 5                        | 1                         | 0                           |
| JacksonCore        | 26                    | 5                | 0                          | 5                            | 5                        | 5                         | 2                           |
| JacksonDatabind    | 112                   | 15               | 0                          | 42                           | 35                       | 13                        | 7                           |
| JacksonXml         | 6                     | 1                | 0                          | 2                            | 3                        | 0                         | 0                           |
| Jsoup              | 93                    | 30               | 0                          | 26                           | 19                       | 8                         | 10                          |
| JxPath             | 22                    | 1                | 0                          | 25                           | 5                        | 7                         | 2                           |
| Lang               | 64                    | 13               | 0                          | 26                           | 25                       | 0                         | 0                           |
| Math               | 106                   | 24               | 0                          | 32                           | 42                       | 7                         | 1                           |
| Mockito            | 38                    | 8                | 0                          | 10                           | 4                        | 2                         | 1                           |
| Time               | 26                    | 3                | 0                          | 13                           | 6                        | 3                         | 1                           |
| Overall            | 835                   | 165              | 0                          | 298                          | 244                      | 84                        | 44


## Extended Categorization for 372 Multi-Hunk bugs in the Defects4J Dataset
### Summary of Types and Counts

| Type                                      | Count |
|-------------------------------------------|-------|
| Single-File within Method : 2 hunks       | 116   |
|   - Of which, single method               | 72    |
|   - Two methods                           | 43    |
|   - Three methods                         | 1     |
|                                           |       |
| Single File within Method : >=3 hunks     | 57    |
|   - Of which, single method               | 22    |
|   - Two methods                           | 12    |
|   - Three methods                         | 14    |
|   - >=4 methods                           | 19    |
|                                           |       |
| Single File not within Method             | 71    |
|                                           |       |
| Cross-File within Method : 2 hunks        | 29    |
|   - Of which, two methods                 | 29    |
|                                           |       |
| Cross-File within Method : >=3 hunks      | 35    |
|   - Of which, two methods                 | 9     |
|   - Three methods                         | 13    |
|   - >=4 methods                           | 13    |
|                                           |       |
| Cross-File not within Method              | 64    |
|                                           |       |
| **Total**                                 | **372** |
