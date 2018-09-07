
# TODO: Add grading warnings.
# TODO: Rethink these. What about cheating...


class GradingError(Exception):
    def __init__(self, student_x500, message):
        self.x500 = student_x500
        self.message = message

    def __str__(self):
        return "{} for {}: {}".format(self.__class__.__name__, self.x500, self.message)


class GroupGradingError(GradingError):
    def __init__(self, student_x500s, message):
        self.x500s = student_x500s
        self.x500 = student_x500s[0]
        self.message = message

    def __str__(self):
        return "{} for {}: {}".format(self.__class__.__name__, self.x500s, self.message)


class FetchError(GradingError):
    pass


class GroupFetchError(GroupGradingError):
    pass


class InvalidSubmissionError(GradingError):
    pass
