from . import default_runner


class AsciidoctorToHTMLConverter:
    """Asciidoctor reader with the same API than :func:`open`."""

    def __init__(self, run=default_runner):
        self.run = run
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

        return self.run(cmdline).stdout


def look_for_title(html):
    try:
        return html.body.select_one('h1').text
    except AttributeError:
        return None


def look_for_introduction(html):
    try:
        return html.body.select_one('#preamble').text.strip()
    except AttributeError:
        return None


def look_for_content(html):
    try:
        return ''.join(str(child) for child in html.body.find_all())
    except AttributeError:
        return None


def look_for_category(html):
    try:
        return html.head.select_one('meta[name=description]')['content']
    except (KeyError, TypeError):
        return None


def look_for_tags(html):
    try:
        tags = html.head.select_one('meta[name=keywords]')['content']
    except (KeyError, TypeError):
        return list()

    return tags.split(', ')
