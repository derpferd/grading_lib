import json


class Writeup:
    def __init__(self, sections=None):
        if sections is None:
            sections = []
        self.sections = []
        for section in sections:
            self.sections += [{**section, "id": "writeup-section-{}".format(len(self.sections))}]

    def __add__(self, other):
        return Writeup(self.sections + other.sections)

    def add_section(self, name, text, html=None):
        if html is None:
            html = "<pre><code>{}</code></pre>".format(text)
        self.sections += [{"id": "writeup-section-{}".format(len(self.sections)),
                           "name": name, "text": text, "html": html}]

    def save(self, filename):
        with open(filename + ".json", "w") as fp:
            json.dump(self.sections, fp)
        section_strs = []
        for section in self.sections:
            section_strs += ["=== {}\n{}".format(section["name"], section["text"])]
        with open(filename + ".txt", "w") as fp:
            fp.write("\n\n".join(section_strs))
