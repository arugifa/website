class AsciidoctorToHTMLConverter:
    def __init__(self, executor):
        self.executor = executor
        self.path = None

    def __call__(self, path):
        self.path = path
        return self

    def read(self):
        cmdline = (
            'asciidoctor '
            '--no-header-footer '
            '-a showtitle=true '
            '--out-file - '
            f'{self.path}')

        process = self.executor.run(cmdline, hide='stdout')
        return process.stdout
