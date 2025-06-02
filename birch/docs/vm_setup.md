# Virtual Machine Set up

### Our Virtual Machines
| VM | Address |
|-----------|----------|
| VM 1 | ec2-user@ec2-54-149-197-123.us-west-2.compute.amazonaws.com  | 
| VM 2 | ec2-user@ec2-34-219-52-76.us-west-2.compute.amazonaws.com  | 

## Initial Set Up
### How to run the experiments from EC2 instances
1. Open an SSH client.

2. Locate your private key file. The key used to launch this instance is `code-repair-ssh-key.pem`
(I have shared the key over slack, please do not share it with anyone else. Also please do not push it to GitHub.)

3. Run this command
`chmod 400 "code-repair-ssh-key.pem"`

4. Place the key in your .ssh directory
`mv code-repair-ssh-key.pem ~/.ssh/`

5. Connect to your instance using its Public DNS: `ec2-54-149-197-123.us-west-2.compute.amazonaws.com`

```
ssh -i "~/.ssh/code-repair-ssh-key.pem" ec2-user@ec2-54-149-197-123.us-west-2.compute.amazonaws.com
```

#### We have two VMs for running experiments:
- VM1
```
ssh -i "~/.ssh/code-repair-ssh-key.pem" ec2-user@ec2-54-149-197-123.us-west-2.compute.amazonaws.com
```

- VM2
```
ssh -i "~/.ssh/code-repair-ssh-key.pem" ec2-user@ec2-34-219-52-76.us-west-2.compute.amazonaws.com
```

## VM Configurations
To configure the virtual machines so that we can run our experiments on them, we need to do the following:

### Setting up Conda
- Run `wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh`
- Set up according to the conda installer.
- Run `source ~/miniconda3/bin/activate` to activate conda after installation
- Check installation with command `conda --version`

### Setting up our Conda Env:
- Run `conda env create -f llm-code-repair-env.yml`

### Setting up AWSCLI:
Create a new profile in `~/.aws/credentials`:
```
❯ cat ~/.aws/credentials
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

### Installing Modules:
Run the following commands:
- `pip install toml`
- `sudo yum install git`
- `git clone https://github.com/rjust/defects4j.git` in the `~/` directory
- `sudo yum install svn`
- `sudo yum install perl`
- `sudo yum install java-1.8.0-amazon-corretto-devel`
- `curl -L https://cpanmin.us | perl - --sudo App::cpanminus`
- `sudo cpan` to enter CPAN terminal
- In CPAN terminal, run `install DBI`, then `exit` to exit the terminal.
- `cd` into `defects4j` directory
- Run `cpanm --installdeps .` in `d4j` directory
- Run `./init.sh` in `d4j` directory
- Run `export PATH=$PATH:"path2defects4j"/framework/bin` ("path2defects4j" points to the directory to which you cloned Defects4J)

After completing all these steps, your vm is ready to run the program.

