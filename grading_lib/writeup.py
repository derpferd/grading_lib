import json
from enum import IntEnum


class Priority(IntEnum):
    Top = 1
    Error = 20
    Answers = 25
    Info = 50
    Debug = 100
    Bottom = 999


class Writeup:
    def __init__(self, sections=None):
        if sections is None:
            sections = []
        self.sections = [s.copy() for s in sections]
        self.__sort()

    def __add__(self, other):
        return Writeup(self.sections + other.sections)

    def __sort(self):
        self.sections.sort(key=lambda x: x['priority'])

    def add_section(self, name, priority: Priority, text, html=None):
        if html is None:
            html = "<pre><code>{}</code></pre>".format(text)
        self.sections += [{"name": name, "text": text, "html": html, 'priority': int(priority)}]
        self.__sort()

    def save(self, filename):
        with open(filename + ".json", "w") as fp:
            json.dump(self.sections, fp)
        section_strs = []
        for section in self.sections:
            section_strs += ["=== {}\n{}".format(section["name"], section["text"])]
        with open(filename + ".txt", "w") as fp:
            fp.write(bytes("\n\n".join(section_strs), encoding='utf8').decode('utf8', 'surrogateescape'))
