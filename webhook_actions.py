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
        self.enabled = True

    def get_enabled(self, name):
        if self.name == name:
            return self.enabled
    
    def enable(self, name):
        if self.name == name or name == None:
            self.enabled = True
    
    def disable(self, name):
        if self.name == name or name == None:
            self.enabled = False

    def check(self, input: str):
        match = re.search(self.regex, input)
        if match and self.enabled:
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
        self.enabled = [True for _ in on_match]
    
    def get_enabled(self, name):
        for action in self.match_list:
            if action.__name__ == name:
                return self.enabled[self.match_list.index(action)]
    
    def enable(self, name):
        for action in self.match_list:
            if action.__name__ == name or name == None:
                self.enabled[self.match_list.index(action)] = True
    
    def disable(self, name):
        for action in self.match_list:
            if action.__name__ == name or name == None:
                self.enabled[self.match_list.index(action)] = False

    def check(self, input: str):
        for regex in self.regexes:
            match = re.search(regex, input)
            if match and self.enabled[self.regexes.index(regex)]:
                return match, self.match_list[self.regexes.index(regex)]
        
        return None

class action_list:
    """
        Holds a list of regex_actions and checks them all for matches given an input string.
        Grants the ability to dynamically enable and/or disable actions.
    """
    
    def __init__(self, actions: list):
        self.all_actions = actions
    
    # Find the first action that matches the input string, return it and the match.
    def check(self, input: str):
        for action in self.enabled_actions:
            match = action.check(input)
            if match:
                LOG.debug(f"Got match ({match[0][0]})!")
                return match[0], match[1] # Return the match, and the function to run.
        
        return None # Just here so we can note that if it fails it returns nothing.

    def get_enabled(self, name: str):
        for action in self.all_actions:
            enabled = action.get_enabled(name)
            if type(enabled) == bool:
                return enabled
    
    # Enable an action by name.
    def enable_action(self, name: str):        
        for action in self.all_actions:
            action.enable(name)
    
    # Disable an action by name.
    def disable_action(self, name: str):
        for action in self.all_actions:
            action.disable(name)
    
    # Enable all actions.
    def enable_all(self):
        for action in self.all_actions:
            action.enable()
    
    # Disable all actions.
    def disable_all(self):
        for action in self.all_actions:
            action.disable()