import json
import os
from collections import defaultdict
from typing import Dict, Optional


class StudentReview:
    def __init__(self, x500: str, scores: Dict[str, int]):
        self.x500 = x500
        self.scores = defaultdict(int)
        self.scores.update(scores)

    def set(self, question_name: str, score: int):
        self.scores[question_name] = score

    def get(self, question_name: str):
        return self.scores[question_name]

    @property
    def score(self):
        return sum(self.scores.values())

    @classmethod
    def from_obj(cls, obj):
        return cls(obj['x500'], obj['scores'])

    @property
    def obj(self):
        return {'x500': self.x500,
                'score': self.score,
                'scores': dict(self.scores)}


class ReviewDB:
    def __init__(self, root_dir: str = 'data/review'):
        self.root_dir = root_dir

        if not os.path.exists(root_dir):
            os.mkdir(root_dir)

    @property
    def records(self) -> Dict[str, StudentReview]:
        records = {}
        for file in os.listdir(self.root_dir):
            with open(os.path.join(self.root_dir, file), 'r') as fp:
                obj = json.load(fp)
                record = StudentReview.from_obj(obj)
                records[record.x500] = record
        return records

    def get(self, x500) -> StudentReview:
        path = os.path.join(self.root_dir, x500)
        if os.path.exists(path):
            with open(path, 'r') as fp:
                obj = json.load(fp)
                return StudentReview.from_obj(obj)
        else:
            return StudentReview(x500, {})

    def save(self, record: StudentReview):
        with open(os.path.join(self.root_dir, record.x500), 'w') as fp:
            json.dump(record.obj, fp)
