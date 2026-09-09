# AP Script

Just some scripts to help me learn python. Used to look at Archipelago data

[`get-room-data.py`](get-room-data.py) - Gets data for an Archipelago room and stores to json  
[`make-hint-graph.py`](make-hint-graph.py) - Make a hint graph using the room data from above. Has a good number of options to 

# Setup
```bash
# First time setup

# Install some packages that are used by the hint graph script
sudo apt install graphviz libgraphviz-dev

# Setup a python virtual environment
python -m venv .venv
pip install -r requirements.txt
source .venv/bin/activate
```

```bash
# After first time setup is complete and opening a new terminal
source .venv/bin/activate
```
