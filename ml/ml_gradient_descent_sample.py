def gradient_descent(x, y, theta, learning_rate, iteration):
    x = np.c_[np.ones((len(x), 1)), x]
    for _ in range(iteration):
        pred = np.dot(x,theta)
        theta = theta - 1 / len(y) * learning_rate * (x.T.dot(pred - y))
    return theta