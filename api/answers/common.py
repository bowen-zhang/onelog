import abc
import json
import re

def question(template):
    def create_from(cls, query):
        for question in cls._questions:
            m = question.match(query)
            if m:
                print m.groupdict()
                return cls(**m.groupdict())
        return None

    def wrapper(cls):
        try:
            x = cls._questions
        except:
            cls._questions = []
            cls.create_from = classmethod(create_from)
        cls._questions.append(re.compile(template))
        return cls
    return wrapper

def answer(short_title, full_title):
    def new_answer(self):
        rlt = self._original_answer()
        return Answer(
            short_title=short_title,
            full_title=full_title,
            short_answer=rlt.short_answer,
            full_answer=rlt.full_answer,
            details=rlt.details)

    def wrapper(cls):
        cls._original_answer = cls.answer
        cls.answer = new_answer
        return cls

    return wrapper


class Question(object):
    
    @abc.abstractmethod
    def answer(self):
        pass


class Answer(object):
    
    def __init__(self, short_title=None, full_title=None, short_answer=None, full_answer=None, details=None):
        self._short_title = short_title
        self._full_title = full_title
        self._short_answer = short_answer
        self._full_answer = full_answer
        self._details = details

    @property
    def short_title(self):
        return self._short_title

    @property
    def full_title(self):
        return self._full_title

    @property
    def short_answer(self):
        return self._short_answer

    @property
    def full_answer(self):
        return self._full_answer

    @property
    def details(self):
        return self._details

    def to_json(self):
        return json.dumps({
            'short_title': self.short_title,
            'full_title': self.full_title,
            'short_answer': self.short_answer,
            'full_answer': self.full_answer,
            'details': self.details,
            })


