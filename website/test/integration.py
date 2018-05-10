from subprocess import PIPE, Popen, run


class CommandLine:
    """Execute a program with :mod:`subprocess`."""

    def __init__(self, program):
        self.program = program

    def get_command_line(self, arguments):
        cmdline = arguments.split()
        cmdline.insert(0, self.program)
        return cmdline

    def run(self, arguments, **kwargs):
        cmdline = self.get_command_line(arguments)
        return run(cmdline, **kwargs)

    def run_with_popen(self, arguments, **kwargs):
        cmdline = self.get_command_line(arguments)
        return Popen(cmdline, **kwargs)


class InvokeStub:
    """To be injected in functions or methods depending on Invoke context."""

    @staticmethod
    def run(cmdline, **kwargs):
        cmdline = cmdline.split()
        return run(cmdline, stdout=PIPE, universal_newlines=True)
