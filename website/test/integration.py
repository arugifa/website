from subprocess import PIPE, run


class CommandLine:
    def __init__(self, program):
        self.program = program

    def run(self, cmdline, **kwargs):
        cmdline = cmdline.split()
        cmdline.insert(0, self.program)
        run(cmdline, **kwargs)


class InvokeContextStub:
    @staticmethod
    def run(cmdline, **kwargs):
        cmdline = cmdline.split()
        return run(cmdline, stdout=PIPE, universal_newlines=True)
