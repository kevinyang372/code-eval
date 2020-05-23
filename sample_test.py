from base import BaseTest

# class TestCases(BaseTest):

#     def __init__(self, func):
#         super().__init__(func)
#         self.parameters = {
#             'three_way_merge': [([[2,3,4,5]]), ([[4,3,5,2]]), ([[5,4,3,2]]), ([[4,5,3,2]])],
#             'extended_three_way_merge': [([[2,3,4,5]]), ([[4,3,5,2]]), ([[5,4,3,2]]), ([[4,5,3,2]])],
#             'bucket_sort': [([[2,3,4,5]]), ([[4,3,5,2]]), ([[5,4,3,2]]), ([[4,5,3,2]])],
#             'extended_bucket_sort': [([[2,3,4,5]]), ([[4,3,5,2]]), ([[5,4,3,2]]), ([[4,5,3,2]])],
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
            'func': [(2, 3), (4, 5), (6, 7)],
            'func2': [(2, 3), (4, 5), (6, 7)]
        }
        self.answers = {
            'func': [5, 9, 13],
            'func2': [6, 20, 42]
        }