import argparse
import sys


class HelpCall(Exception):
    def __init__(self, message):
        """ Constructor method
        This exception ist made to be catched by papistui.tui.handle_command in order
        to by distinguished from other parsing errors. Help message will then be
        displayed in the commandinfo window

        :param message: the error message to be catched
        """

        self.message = message
        super().__init__(self.message)

    def helpmessage(self):
        """ Return help message saved when object is instantiated

        :return list of strings comprising help information
        """

        message = str(self)
        message = message.splitlines()[2:]
        return message


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        """ Raise exception on every error that is not help call

        :param message: str catch message
        :raises Exception
        """

        raise Exception(message)

    def print_help(self):
        """
        Overwrite print_help message so it does not mess up curses and raise HelpCall Exception instead

        :raises HelpCall
        """

        raise HelpCall(self.format_help())
