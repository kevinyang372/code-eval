def expectation_maximization(heads, throws, iteration, thetas):

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