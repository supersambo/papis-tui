from nvr.nvr import Nvr
import psutil
import subprocess


class Vim:
    def __init__(self, flavour="vim"):
        """ Constructor method

        :param flavour: str either vim or nvim, defaults to "vim"
        """

        self.flavour = flavour
        self.servername = None
        self.nvr = None

    def get_servers(self):
        """ Detect available (n)vim servers

        :return list of servernames
        """

        if self.flavour == "vim":
            try:
                servers = subprocess.check_output(["vim", "--serverlist"])
                servers = servers.decode("utf-8").splitlines()
            except subprocess.SubprocessError:
                pass

        elif self.flavour == "nvim":
            servers = []
            for proc in psutil.process_iter(attrs=["name"]):
                if proc.info["name"] == "nvim":
                    try:
                        for conn in proc.connections("inet4"):
                            servers.insert(0, ":".join(map(str, conn.laddr)))
                        for conn in proc.connections("inet6"):
                            servers.insert(0, ":".join(map(str, conn.laddr)))
                        try:
                            for conn in proc.connections("unix"):
                                if conn.laddr:
                                    servers.insert(0, conn.laddr)
                        except FileNotFoundError:
                            # Windows does not support Unix domain sockets and WSL1
                            # does not implement /proc/net/unix
                            pass
                    finally:
                        pass

        if servers:
            return list(dict.fromkeys(servers))

    def set_server(self, servername):
        """ Set server to be used upon next send

        :param servername: str name of server
        """

        if self.flavour == "vim":
            self.servername = servername

        elif self.flavour == "nvim":
            self.servername = servername
            self.nvr = Nvr(servername)
            self.nvr.attach()

    def check_server(self):
        """ Check whether server set before is still available

        :return boolean True when available
        """

        servers = self.get_servers()
        if self.servername is not None and self.servername in servers:
            return True
        else:
            self.servername = None
            self.nvr = None
            return False

    def send(self, string):
        """ Send a string to be evaluated to (n)vim server

        :param string: string to be evaluated and sent
        """

        if self.flavour == "vim":
            sendline = (
                f'vim --servername {self.servername} '
                f'--remote-send "<Esc>a{string}"'
            )
            _ = subprocess.call(sendline, shell=True)
        if self.flavour == "nvim":
            sendline = f"<Esc>a{string}"
            self.nvr.server.input(sendline)
