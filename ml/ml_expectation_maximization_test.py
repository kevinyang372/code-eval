from base import BaseTest
import numpy as np

class TestCases(BaseTest):

    def __init__(self, func):
        super().__init__(func)

        self.parameters = { 'expectation_maximization': [] }
        self.answers = { 'expectation_maximization': [] }

        heads = [14, 33, 19, 10, 0, 17, 24, 17, 1, 36, 5, 6, 5, 13, 4, 35, 5, 5, 74, 34]
        throws = [41, 43, 23, 23, 1, 23, 36, 37, 2, 131, 5, 29, 13, 47, 10, 58, 15, 14, 100, 113]
        iteration = 10
        init_thetas = [[0.4, 0.6], [0.6, 0.4]]

        comb = (heads, throws, iteration, init_thetas)
        self.parameters['expectation_maximization'].append(comb)
        self.answers['expectation_maximization'].append(self.em(*comb))


    def em(self, heads, throws, iteration, thetas):

        trials = [(x, y - x) for x, y in zip(heads, throws)]

        for _ in range(iteration):

            vs_A = []
            vs_B = []

            for x in trials:

                ll_a = np.sum([x * np.log(thetas[0])])
                ll_b = np.sum([x * np.log(thetas[1])])

                denom = np.exp(ll_a) + np.exp(ll_b)

                w_A = np.exp(ll_a) / denom
                w_B = np.exp(ll_b) / denom

                vs_A.append(np.dot(w_A, x))
                vs_B.append(np.dot(w_B, x))

            thetas[0] = np.sum(vs_A, 0) / np.sum(vs_A)
            thetas[1] = np.sum(vs_B, 0) / np.sum(vs_B)

        return thetas