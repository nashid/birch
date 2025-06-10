### Environment setup
```
conda env create -n llm-code-repair-env --file llm-code-repair-env.yml
```

#### Environment setup for Claude models on Bedrock (from scratch)

##### Step 1: create a new conda environment
```
conda create --name llm-code-repair-env python=3.12.3
```

##### Step 2: activate the environment
```
conda activate llm-code-repair-env
```

##### Step 3: export the dependencies to a file
```
conda env export --no-builds | grep -v "^prefix: " > llm-code-repair-env.yml
```

##### Step 4: install the dependencies
```
conda env create --name llm-code-repair-env --file llm-code-repair-env.yml
```

### Defects4J Setup
To use Defects4J, clone and install it by following the official instructions. 
Our tool was tested using **Defects4J version 2.0.1**.

After installation, add Defects4J's executables to your `PATH` environment variable. Run the following command:
```
export PATH=$PATH:"path_to_defects4j"/framework/bin
```

Here, `path_to_defects4j` should point to the directory where you installed Defects4J (e.g., `/user/yourComputerUserName/desktop/defects4j`).

Once configured, verify the setup by running:
```
defects4j
```
If the setup is successful, the Defects4J usage instructions will be displayed.

### Setting up the bedrock environment
It is handy to install `awscli`:

`brew install awscli`

Create a new profile in `~/.aws/credentials`:
```
❯ cat ~/.aws/credentials
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

**Please dont push the AWS access key and secret to GitHub.**