import subprocess
import re

def get_tmux_pid(tmux_session_name: str):
    """
      Get a tree of PIDs to process names of all processes in the given tmux
      session using the `tmux_pid.sh` file

      Example output of tmux_pid.sh:
      ===== session $0:session_name =====
      bash,17209
        `-bash,17248
            `-java,17249 -jar forge-1.16.5-36.2.39.jar nogui
                |-{java},17250
                |-{java},17251
                `-{java},17544

      bash,17227
        `-python3,17239 webhook.py
    """

    # Get the output of the tmux_pid.sh file.
    output = subprocess.run(["utilities/tmux_pid.sh"], stdout=subprocess.PIPE).stdout.decode("utf-8")

    # Split the output into lines.
    lines = output.split("\n")

    # Get the line that starts with the session name.
    session_line = None
    for i in range(0, lines.length):
        line = lines[i]
        for j in range(0, 10):
            search = f"===== session ${j}:{tmux_session_name} ====="
            if line.startswith(search):
                session_line = i
                break
        
        if session_line:
            break
    
    if not session_line:
        raise Exception(f"Could not find session {tmux_session_name} in tmux_pid.sh output.")
    
    # Get the lines that are children of the session line.
    children = []
    for i in range(session_line + 1, lines.length):
        line = lines[i]
        if line.startswith("===== session"):
            break
        children.append(line)

    def new_node():
        return {
            "process_name": "",
            "pid": "",
            "_leading_spaces": 0,
            "children": [],
            "parent": None,
            "arguments": ""
        }

    # Parse the children into a tree.
    tree = new_node()
    current_node = tree

    # Splits a line into 4 groups:
    #   1. Leading spaces
    #   2. Process name
    #   3. PID
    #   4. Arguments
    line_re = r"^(\s*)['`|-]['`|-](.+?),(\d+) ?(.*?)$"

    # We want to save the arguments as well, if any.

    for child in children:
        match = re.match(line_re, child)
        if not match:
            # There may be blank lines, we don't care about those.
            continue
        
        leading_spaces = match.group(1)
        process_name = match.group(2)
        pid = match.group(3)
        arguments = match.group(4)

        # Get the number of leading spaces.
        leading_spaces_count = len(leading_spaces)

        # If the number of leading spaces is less than the current node, we
        # need to go back up the tree.
        if leading_spaces_count < current_node["_leading_spaces"]:
            # Repeatedly grab the parent node until the leading space count is below, or the parent is null.
            while current_node["_leading_spaces"] > leading_spaces_count and current_node["parent"]:
                current_node = current_node["parent"]
        
        # If the number of leading spaces is greater than the current node, we
        # should create a new child node.
        elif leading_spaces_count > current_node["_leading_spaces"]:
            new_child = new_node()
            new_child["parent"] = current_node
            current_node["children"].append(new_child)
            current_node = new_child
        
        # If the number of leading spaces is equal to the current node, we
        # don't need to do anything.

        # Set the current node's values.
        current_node["process_name"] = process_name
        current_node["pid"] = pid
        current_node["_leading_spaces"] = leading_spaces_count
        current_node["arguments"] = arguments
    

    
