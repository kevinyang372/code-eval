from base import BaseTest


class TestCases(BaseTest):

    def __init__(self, func):
        super().__init__(func)
        self.parameters = {
            'bubble_sort': [([2, 3, 4, 5],), ([4, 3, 5, 2],), ([5, 4, 3, 2],), ([4, 5, 3, 2],)],
            'selection_sort': [([2, 3, 4, 5],), ([4, 3, 5, 2],), ([5, 4, 3, 2],), ([4, 5, 3, 2],)],
        }
        self.answers = {
            'bubble_sort': [[2, 3, 4, 5], [2, 3, 4, 5], [2, 3, 4, 5], [2, 3, 4, 5]],
            'selection_sort': [[2, 3, 4, 5], [2, 3, 4, 5], [2, 3, 4, 5], [2, 3, 4, 5]],
        }
