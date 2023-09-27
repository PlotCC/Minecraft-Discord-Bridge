from __future__ import annotations
import re
import time
import os
import logging

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable

from webhook_bridge import Bridge
import config

filesize = 0

LOG = logging.getLogger("WEBHOOK_ACTIONS")

def need_log_reopen():
    global filesize
    if not os.path.isfile(config.webhook["latest_log_location"]):
        LOG.info("Reopen required.")
        return True
    new_size = os.path.getsize(config.webhook["latest_log_location"])
    old_size = filesize
    filesize = new_size

    return new_size < old_size


def open_latest_log():
    printed = False
    lll = config.webhook["latest_log_location"]
    while not os.path.isfile(lll):
        if not printed:
            LOG.info(f"Waiting for latest.log to exist ({lll}).")
        printed = True
        time.sleep(0.1)

    LOG.info("Log opened.")
    return open(lll)


class regex_action:
    """Holds a regex and runs a function if the regex matches an input string"""

    def __init__(self, regex: str, on_match):
        self.regex = regex
        self.on_match = on_match
        self.name = on_match.__name__

    def check(self, input: str):
        match = re.search(self.regex, input)
        if match:
            LOG.debug(f"Got match ({self.name})!")
            return match, self.on_match

        return None
    
class multi_regex_action:
    """
        Uses a linked list of regex and functions to run if the regex matches an input string.
        This is mostly used to ensure a specific order of tests for some regexes.
    """

    def __init__(self, regexes: list[str], on_match: list[Callable]):
        self.regexes = regexes
        self.match_list = on_match
        self.name = on_match.__name__

    def check(self, input: str):
        for regex in self.regexes:
            match = re.search(regex, input)
            if match:
                LOG.debug(f"Got match ({self.name})!")
                return match, self.match_list[self.regexes.index(regex)]
        
        return None

class action_list:
    """
        Holds a list of regex_actions and checks them all for matches given an input string.
        Grants the ability to dynamically enable and/or disable actions.
    """
    
    def __init__(self, actions: list):
        self.all_actions = actions
        self.enabled_actions = []
        self.disabled_actions = []
    
    # Find the first action that matches the input string, return it and the match.
    def check(self, input: str):
        for action in self.enabled_actions:
            match = action.check(input)
            if match:
                return match[0], match[1] # Return the match, and the function to run.
        
        return None # Just here so we can note that if it fails it returns nothing.
    
    # Enable an action by name.
    def enable_action(self, name: str):
        for action in self.disabled_actions:
            if action.name == name:
                self.enabled_actions.append(action)
                self.disabled_actions.remove(action)
                return
        
        for action in self.all_actions:
            if action.name == name:
                self.enabled_actions.append(action)
                return
    
    # Disable an action by name.
    def disable_action(self, name: str):
        for action in self.enabled_actions:
            if action.name == name:
                self.disabled_actions.append(action)
                self.enabled_actions.remove(action)
                return
        
        for action in self.all_actions:
            if action.name == name:
                self.disabled_actions.append(action)
                return
    
    # Enable all actions.
    def enable_all(self):
        self.enabled_actions = self.all_actions
        self.disabled_actions = []
    
    # Disable all actions.
    def disable_all(self):
        self.disabled_actions = self.all_actions
        self.enabled_actions = []