import tokenize


def preprocess(s):
    return s.replace(' ', '').replace('\n', '').replace('#', '').replace('\"', '')


if __name__ == '__main__':

    comments = ["", ""]
    with tokenize.open("similar_code1.py") as f:
        tokens_1 = tokenize.generate_tokens(f.readline)
        for token in tokens_1:
            if token.exact_type in (3, 60):
                comments[0] += preprocess(token.string)

    with tokenize.open("similar_code2.py") as f:
        tokens_2 = tokenize.generate_tokens(f.readline)
        for token in tokens_2:
            if token.exact_type in (3, 60):
                comments[1] += preprocess(token.string)

    print(comments)
