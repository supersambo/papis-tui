import re
from curses.ascii import alt, ctrl


class KeyMappings:
    def __init__(self, config, filtered=None):
        """ Constructor method

        :param config: dict configuration options
        :param filtered: list of mappings to be used (for picker selector),
            defaults to None
        """

        mappings = {}
        for i in config["keymappings"]:
            if type(config["keymappings"][i]) is list:
                mappings.update({i: config["keymappings"][i]})
            else:
                mappings.update(
                    {i: (config["keymappings"][i], config["keymappings"][i])}
                )

        self.keymappings = []
        for m in mappings.keys():
            parsed = self.parse_keymapping(m)
            mapping = {"km": m, "cmd": mappings[m][0], "cmd_desc": mappings[m][1]}
            keys = []
            codes = []
            for k in parsed:
                keys.append(k)
                codes.append(self.get_keycode(k))

            mapping.update({"keys": keys})
            mapping.update({"codes": codes})
            if filtered:
                if mapping["cmd"].split(" ")[0] in filtered:
                    self.keymappings.append(mapping)
            else:
                self.keymappings.append(mapping)

    def find(self, keys):
        """ Find keymappings that start with provided keys (partial match)

        :param keys: list of keys
        :returns list of matching keymappings
        """

        result = []
        for keymapping in self.keymappings:
            if keys == keymapping["codes"][: len(keys)]:
                keys_typed = "".join(keymapping["keys"][: len(keys)])
                keys_opt = "".join(keymapping["keys"][len(keys) :])
                keymapping.update({"keys_typed": keys_typed, "keys_opt": keys_opt})
                result.append(keymapping)

        return result

    def match(self, keys):
        """ Find keymapping that matches provided keys exactly

        :param keys: list of keys
        """

        for keymapping in self.keymappings:
            if keys == keymapping["codes"]:
                return keymapping

    def check(self, command, keys):
        """ Check whether keys are mapped to a specific command

        :param command: command to be matched
        :param keys: list of keys
        :return bool whether keys are mapped to command
        """

        for keymapping in self.keymappings:
            if keymapping["cmd"].startswith(command) and keymapping["codes"] == keys:
                return True

        return False

    def items(self):
        """ Return list of tuples keys and command description
        command description is either command itself or description provide in config

        :return list of tuples (keys, description)
        """
        result = []
        for i in self.keymappings:
            result.append((i["km"], i["cmd_desc"]))

        return result

    def parse_keymapping(self, string):
        """ Parse key representation from config file

        :param string: str key representation
        :result list of either singly character or modified keygroups
        """
        idx = 0
        result = []
        while idx < len(string):
            if string[idx] == "<":
                keymod = re.sub(r">.*$", "", string[idx + 1 :])
                result.append(keymod)
                idx += len(keymod) + 2
            else:
                result.append(string[idx])
                idx += 1

        return result

    def get_keycode(self, key):
        """ Return keycode for a string representation of a key

        :param key: str can either be a single character or representation of
                    modified key like <ctrl-a> or <alt-a>
        :return int keycode
        """
        import curses

        lkey = key.lower()
        result = None
        if len(key) > 1:
            if "-" in key:
                if lkey.startswith("ctrl-") or lkey.startswith("c-"):
                    result = ctrl(ord(key[len(key) - 1]))
                elif lkey.startswith("alt-") or lkey.startswith("a-"):
                    result = alt(ord(key[len(key) - 1]))
            elif lkey.startswith("key_"):
                result = getattr(curses, key.upper(), None)
        else:
            result = ord(key)

        return result
