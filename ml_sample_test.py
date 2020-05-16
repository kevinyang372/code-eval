from base import BaseTest
import numpy as np

class TestCases(BaseTest):

    def __init__(self, func):
        super().__init__(func)

        self.parameters = { 'gradient_descent': [] }
        self.answers = { 'gradient_descent': [] }

        for _ in range(5):
            
            x_data = 2 * np.random.rand(100, 1)
            y_data = 4 + 3 * x_data + np.random.randn(100,1)

            init_theta = np.random.randn(2, 1)
            learning_rate = 0.01
            iteration = 500

            comb = (x_data, y_data, init_theta, learning_rate, iteration)
            self.parameters['gradient_descent'].append(comb)

            temp = self.gradient_descent(*comb)
            self.answers['gradient_descent'].append(temp)


    def gradient_descent(self, x, y, theta, learning_rate, iteration):
        x = np.c_[np.ones((len(x), 1)), x]
        for _ in range(iteration):
            pred = np.dot(x,theta)
            theta = theta - 1 / len(y) * learning_rate * (x.T.dot(pred - y))
        return theta