from base import BaseTest

# class TestCases(BaseTest):

#     def __init__(self, func):
#         super().__init__(func)
#         self.parameters = {
#             'three_way_merge': [([[2,3,4,5]]), ([[4,3,5,2]]), ([[5,4,3,2]]), ([[4,5,3,2]])],
#             'extended_three_way_merge': [([[2,3,4,5]]), ([[4,3,5,2]]), ([[5,4,3,2]]), ([[4,5,3,2]])],
#             'bucket_sort': [([2,3,4,5], 1), ([4,3,5,2], 1), ([5,4,3,2], 1), ([4,5,3,2], 1)],
#             'extended_bucket_sort': [([2,3,4,5], 1), ([4,3,5,2], 1), ([5,4,3,2], 1), ([4,5,3,2], 1)]
#         }
#         self.answers = {
#             'three_way_merge': [[2,3,4,5], [2,3,4,5], [2,3,4,5], [2,3,4,5]],
#             'extended_three_way_merge': [[2,3,4,5], [2,3,4,5], [2,3,4,5], [2,3,4,5]],
#             'bucket_sort': [[2,3,4,5], [2,3,4,5], [2,3,4,5], [2,3,4,5]],
#             'extended_bucket_sort': [[2,3,4,5], [2,3,4,5], [2,3,4,5], [2,3,4,5]]
#         }


class TestCases(BaseTest):

    def __init__(self, func):
        super().__init__(func)
        self.parameters = {
            'add': [(2, 3), (4, 5), (6, 7)],
            'subtract': [(2, 3), (4, 5), (6, 7)],
            'multiply': [(2, 3), (4, 5), (6, 7)]
        }
        self.answers = {
            'add': [5, 9, 13],
            'subtract': [-1, -1, -1],
            'multiply': [6, 20, 42]
        }
