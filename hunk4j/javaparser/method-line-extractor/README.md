# Method Line Extractor

This project uses [JavaParser](https://javaparser.org/) to extract method start and end line numbers from a Java source file and outputs the result in JSON format.

### Running the code
```
mvn clean compile exec:java
```

### Output example
```
[
    {
        "method_name": "sayHello",
        "start_line": 3,
        "end_line": 5
    },
    {
        "method_name": "add",
        "start_line": 7,
        "end_line": 9
    },
    ...
]
```
