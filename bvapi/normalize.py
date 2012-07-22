"""
    normalize.py
    ~~~~~~

    Utility methods for normalizing Bazaarvoice API responses.
"""

import logging

import bvapi
from dictutil import O

log = logging.getLogger('bvapi')

class Normalizer(object):

    TYPE_METADATA = {
        'review':   O({'section': 'Reviews'}),
        'question': O({'section': 'Questions'}),
        'answer':   O({'section': 'Answers'}),
        'story':    O({'section': 'Stories'}),
        'author':   O({'section': 'Authors'}),
        'product':  O({'section': 'Products'}),
        'category': O({'section': 'Categories'}),
    }

    def __init__(self, bvapi, data_type, response, allowed_statuses=None):
        self._bvapi = bvapi
        self._data_type = data_type
        self._response = response
        self._results = response.get('Results', [])
        self._includes = response.get('Includes', {})
        self._allowed_statuses = allowed_statuses

    def normalize(self):
        try:
            if not self._response.HasErrors:
                md = self.TYPE_METADATA[self._data_type]
                # add the Results section to the Includes dictionary so we can resolve back references (eg. Answer.QuestionId -> Question)
                self._includes[md.section] = dict([(o.Id, o) for o in self._results])
                # normalize all the objects in the Results section.  this will, in turn, normalize all referenced objects in the Includes section
                normalize_fn = getattr(self, self._data_type)
                self._response.Results = self._filter(map(normalize_fn, self._results))
            return self._response
        except (TypeError, KeyError) as e:
            # note: this could get quite noisy if it happens frequently...
            log.error('API returned bad data: %s', self._response, exc_info=True)
            return O({ 'HasErrors': True, 'TotalResults': 0, 'Limit': 0, 'Offset': 0, 'Results': [] })

    def question(self, question):
        if self._visit(question):
            self._normalize_timestamps(question)
            self._normalize_subjectreference(question)
            self._normalize_authorreference(question)
            if question.AnswerIds:
                question.Answers = self._filter([self.answer(self._lookup('Answers', id)) for id in question.AnswerIds])
        return question

    def answer(self, answer):
        if self._visit(answer):
            self._normalize_timestamps(answer)
            self._normalize_subjectreference(answer)
            self._normalize_authorreference(answer)
        return answer

    def review(self, review):
        if self._visit(review):
            self._normalize_timestamps(review)
            self._normalize_subjectreference(review)
            self._normalize_authorreference(review)
        return review

    def author(self, author):
        if self._visit(author):
            self._normalize_timestamps(author)
        return author

    def product(self, product):
        if self._visit(product):
            pass
        return product

    def category(self, category):
        if self._visit(category):
            pass
        return category

    def _normalize_authorreference(self, object):
        if object.AuthorId:
            object.Author = self.author(self._lookup('Authors', object.AuthorId))

    def _normalize_subjectreference(self, object):
        if object.ProductId:
            object.Product = self.product(self._lookup('Products', object.ProductId))
        if object.CategoryId:
            object.Category = self.category(self._lookup('Categories', object.CategoryId))
        if object.QuestionId:
            object.Question = self.question(self._lookup('Questions', object.QuestionId))

    def _normalize_timestamps(self, object):
        for key in ('SubmissionTime', 'LastModeratedTime', 'LastModificationTime'):
            if key in object and object[key]:
                object[key] = bvapi.parse_timestamp(object[key])

    def _lookup(self, section, id):
        if section not in self._includes:
            self._includes[section] = O({})
        if id not in self._includes[section]:
            self._includes[section][id] = O({ 'Id': id })
        return self._includes[section][id]

    def _filter(self, items):
        if self._allowed_statuses is not None:
            return [item for item in items if item.ModerationStatus is None or item.ModerationStatus in self._allowed_statuses]
        return items

    def _visit(self, obj):
        if obj._normalized:
            return False  # already visited
        obj._normalized = True
        return True  # first time visit
