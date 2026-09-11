# AP Script

Just some scripts to help me learn python. Used to look at Archipelago data

[`get-room-data.py`](get-room-data.py) - Gets data for an Archipelago room and stores to json  
[`make-hint-graph.py`](make-hint-graph.py) - Make a hint graph using the room data from above. Has a good number of options to show the data in different ways
[`create-goal-data.py`](create-goal-data.py) - Parses room data and outputs relevant goal data. Only support Pokemon Emerald for now


# Setup
### First time setup
```bash
# Linux only. Look up your specific package manager if you don't use apt
sudo apt install build-essential graphviz libgraphviz-dev

# Create a python virtual environment
python -m venv .venv

# Start the virtual environment
source .venv/bin/activate # bash
.\.venv\Scripts\Activate.ps1 # powershell

# Upgrade pip
pip install --upgrade pip

# Install python depedencies. Use the file that matches your OS
# Note: mac os is untested. Try using requirements_windows.txt for mac os
pip install -r requirements_linux.txt
pip install -r requirements_windows.txt
```

### Every time you open a new terminal after the first time setup is complete
```bash
source .venv/bin/activate # bash
.\.venv\Scripts\Activate.ps1 # powershell
```

# Run
Run each python script with the `-h` or `--help` argument to see what you can do. Example below
```bash
python get-room-data.py --help
# A bunch of text will follow explaining what the script does and how to use it
```
