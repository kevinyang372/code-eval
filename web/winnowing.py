from pygments.lexers import PythonLexer
from pygments.token import Name, Literal, Text, Comment
import hashlib
import collections


def token_text(text):
    """Tokenize a python file and clean up unnecessary information."""
    tokens = list(PythonLexer().get_tokens(text))
    line_num = loc_tracker = 0
    results = []

    for category, content in tokens:

        # Convert String contents to S
        if category == Literal.String:
            results.append(('S', line_num, loc_tracker))
            loc_tracker += 1
        # Ignore comments, whitespaces, line breaks and doc strings
        elif category in Comment or category in Text or category in Literal.String.Doc:
            pass
        else:
            results.append((content, line_num, loc_tracker))
            loc_tracker += len(content)

        line_num += content.count('\n')

    return results, line_num


def hash_into_num(text):
    """Hash text into numbers using SHA-1"""
    hashval = hashlib.sha1(text.encode('utf-8')).hexdigest()[-4:]
    return int(hashval, 16)


def kgrams(text, k):
    """Pack text into k grams."""
    return [text[i:i + k] for i in range(len(text) - k)]


def generate_fingerprints(arr, window_size=4):
    """Generate fingerprints for a list of hashed values."""
    queue = collections.deque(arr[:window_size])

    def get_min_ind(a):
        return len(a) - 1 - a[::-1].index(min(a))

    m_ind = get_min_ind(list(queue))
    fingerprints = [(min(queue), m_ind)]
    visited = set([m_ind])

    for i in range(len(arr) - window_size):
        queue.popleft()
        queue.append(arr[i + window_size])

        min_ind = i + get_min_ind(list(queue)) + 1
        if min_ind not in visited:
            fingerprints.append((min(queue), min_ind))
            visited.add(min_ind)

    return fingerprints


def backtrack_line_num(ind, token_map, k):
    """Backtrack for the matching line number."""
    i_range = (ind, ind + k)
    min_line = max_line = -1

    for i in range(len(token_map)):
        _, l, loc = token_map[i]

        if loc >= i_range[0] and min_line < 0:
            if loc == i_range[0]:
                min_line = l
            else:
                min_line = token_map[i - 1][1]
        elif loc >= i_range[1] and max_line < 0:
            max_line = token_map[i - 1][1]
            break

    return min_line + 1, max_line + 1


def merge_intervals(arr):
    arr.sort()
    results = []

    for i, j in arr:
        if i > j:
            continue

        if not results:
            results.append((i, j))

        ii, jj = results[-1]
        if i <= jj:
            results[-1] = (ii, max(jj, j))
        else:
            results.append((i, j))
    return results


def winnowing(f1, f2, k=20):
    """Use winnowing algorithm to detect the approximity between two texts."""

    tokens_1, file1_len = token_text(f1)
    tokens_2, file2_len = token_text(f2)

    corpus_1 = ''.join(t[0] for t in tokens_1)
    corpus_2 = ''.join(t[0] for t in tokens_2)

    fingerprints_1 = generate_fingerprints(list(map(hash_into_num, kgrams(corpus_1, k))))
    fingerprints_2 = generate_fingerprints(list(map(hash_into_num, kgrams(corpus_2, k))))

    intervals_1, intervals_2 = [], []

    for f1, i in fingerprints_1:
        for f2, j in fingerprints_2:
            if f1 == f2:
                intervals_1.append(backtrack_line_num(i, tokens_1, k))
                intervals_2.append(backtrack_line_num(j, tokens_2, k))

    i1 = merge_intervals(intervals_1)
    i2 = merge_intervals(intervals_2)

    return i1, i2, sum(b - a + 1 for a, b in i1) / file1_len, sum(b - a + 1 for a, b in i2) / file2_len
