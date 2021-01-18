import tokenize


def preprocess(s):
    """Process the string to clean common characters in comments."""
    return s.replace(' ', '').replace('\n', '').replace('#', '').replace('\"', '')


def edit_distance(s1, s2):
    """Apply levenshtein distance to determine the edit distance between two comment strings."""

    # Initialize dp
    dp = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]

    for i in range(len(dp)):
        for j in range(len(dp[0])):
            if i == 0 and j == 0:
                continue
            elif i == 0:
                dp[i][j] = dp[i][j - 1] + 1
            elif j == 0:
                dp[i][j] = dp[i - 1][j] + 1
            else:
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = min(dp[i - 1][j - 1], dp[i][j - 1], dp[i - 1][j]) + 1

    return dp[-1][-1]


if __name__ == '__main__':

    comments = ["", ""]
    with tokenize.open("similar_code1.py") as f:
        tokens_1 = tokenize.generate_tokens(f.readline)  # Convert code into tokens
        for token in tokens_1:
            if token.exact_type in (3, 60):  # Comment - type 3 and string - type 6
                comments[0] += preprocess(token.string)

    with tokenize.open("similar_code2.py") as f:
        tokens_2 = tokenize.generate_tokens(f.readline)
        for token in tokens_2:
            if token.exact_type in (3, 60):
                comments[1] += preprocess(token.string)

    print(comments)

    d = edit_distance(comments[0], comments[1])
    mx_len = len(max(comments[0], comments[1], key=len))
    print(f"Edit distance {d}, Max length {mx_len}, Ratio {1 - d/mx_len}")
