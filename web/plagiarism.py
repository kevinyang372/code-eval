import ast
import collections
import itertools
import tokenize
from apted import APTED, Config
from io import StringIO

from web.models import User, Result
from web.winnowing import winnowing


class Node:
    def __init__(self, encoding):
        self.value = encoding
        self.children = []


class CustomConfig(Config):
    def rename(self, node1, node2):
        """Compares attribute .value of trees"""
        return 1 if node1.value != node2.value else 0

    def children(self, node):
        """Get left and right children of trees"""
        return [x for x in node.children if x]


class Plagiarism:
    """Receives two result ids and compute all plagiarism related specs."""

    def __init__(self, r1, r2):
        self.r1 = r1
        self.r2 = r2

        self.result_1 = Result.query.filter_by(id=r1).first()
        self.result_2 = Result.query.filter_by(id=r2).first()

        try:
            self.tree_1 = ast.parse(self.result_1.content)
            self.tree_2 = ast.parse(self.result_2.content)
        except Exception as e:
            self.tree_1 = None
            self.tree_2 = None

    #########################
    # Plagiarism Algorithms #
    #########################

    def exact_match(self, node1, node2):
        """Exact match algorithm between two pieces of code."""

        if type(node1) is not type(node2):
            return False
        if isinstance(node1, ast.AST):
            for k, v in vars(node1).items():
                # Skip unrelated information
                if k in ('lineno', 'col_offset', 'ctx', 'end_col_offset', 'end_lineno'):
                    continue
                # Recursively check for child nodes
                if not self.exact_match(v, getattr(node2, k)):
                    return False

            return True
        elif isinstance(node1, list):
            return all(itertools.starmap(self.exact_match, zip(node1, node2)))
        else:
            return node1 == node2

    def unifying_ast_match(self, node1, node2):
        """Unifying ast match detecting naive variable renaming."""

        mapping = {}

        def match(node1, node2):
            if type(node1) is not type(node2):
                return False
            if isinstance(node1, ast.AST):
                if isinstance(node1, ast.Expr):
                    return True

                for k, v in vars(node1).items():
                    if k in ('lineno', 'col_offset', 'ctx', 'end_col_offset', 'end_lineno'):
                        continue

                    # Skip id and name of variables.
                    if k == 'id' or k == 'arg':
                        if v not in mapping:
                            mapping[v] = getattr(node2, k)
                        elif mapping[v] != getattr(node2, k):
                            return False
                    elif not self.unifying_ast_match(v, getattr(node2, k)):
                        return False

                return True
            elif isinstance(node1, list):
                if len(node1) != len(node2):
                    return False
                return all(itertools.starmap(self.unifying_ast_match, zip(node1, node2)))
            else:
                return node1 == node2

        return match(node1, node2)

    def ast_match_ignoring_variables(self, node1, node2):
        """AST matching algorithm completely ignoring variables."""

        if type(node1) is not type(node2):
            return False
        if isinstance(node1, ast.AST):
            for k, v in vars(node1).items():
                if k in ('lineno', 'col_offset', 'ctx', 'id', 'arg', 'name', 'args', 'end_col_offset', 'end_lineno'):
                    continue
                elif not self.ast_match_ignoring_variables(v, getattr(node2, k)):
                    return False

            return True
        elif isinstance(node1, list):
            return all(itertools.starmap(self.ast_match_ignoring_variables, zip(node1, node2)))
        else:
            return node1 == node2

    def edit_distance(self, s1, s2):
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

    def tree_distance(self):
        """Get edit distance between two AST trees using APTED algorithm."""
        if not self.tree_1 or not self.tree_2:
            return 0

        r1, r2 = self.copy_tree(self.tree_1), self.copy_tree(self.tree_2)
        apted = APTED(r1, r2, CustomConfig())

        return 1 - apted.compute_edit_distance() / max(self.get_tree_size(r1), self.get_tree_size(r2))

    def comment_edit_distance(self):
        """Apply string edit distance algorithm on the comment section of the source code."""
        comments = ["", ""]

        tokens_1 = tokenize.generate_tokens(StringIO(self.result_1.content).readline)  # Convert code into tokens
        for token in tokens_1:
            if token.exact_type in (3, 60):  # Comment - type 3 and string - type 6
                comments[0] += self.preprocess(token.string)

        tokens_2 = tokenize.generate_tokens(StringIO(self.result_2.content).readline)
        for token in tokens_2:
            if token.exact_type in (3, 60):
                comments[1] += self.preprocess(token.string)

        d = self.edit_distance(comments[0], comments[1])
        mx_len = len(max(comments[0], comments[1], key=len))

        if mx_len == 0:
            return 0.0

        return 1 - d / mx_len

    #####################
    # Utility Functions #
    #####################

    def preprocess(self, s):
        """Process the string to clean common characters in comments."""
        return s.replace(' ', '').replace('\n', '').replace('#', '').replace('\"', '')

    def copy_tree(self, node, dummy=None):
        t = type(node).__name__

        if 'name' in node._fields:
            t += ':' + node.name
        elif 'id' in node._fields:
            t += ':' + node.id

        curr = Node(t)
        if dummy is not None:
            dummy.children.append(curr)

        for k, v in vars(node).items():
            if isinstance(v, list):
                for p in v:
                    if isinstance(p, ast.AST):
                        self.copy_tree(p, curr)
            elif isinstance(v, ast.AST):
                self.copy_tree(v, curr)

        return curr

    def get_tree_size(self, root):
        """Get size of a tree."""
        return 1 + sum(self.get_tree_size(node) for node in root.children)

    def compile_plagarism_report_two(self):
        """Compare two specific files for plagiarism."""
        if not self.tree_1 or not self.tree_2:
            return []

        comparison = []
        comparison.append(self.exact_match(self.tree_1, self.tree_2))
        comparison.append(self.unifying_ast_match(self.tree_1, self.tree_2))
        comparison.append(self.ast_match_ignoring_variables(self.tree_1, self.tree_2))
        comparison.append(self.comment_edit_distance())

        return comparison

    def winnowing_wrapper(self):
        """AST matching algorithm completely Ignore variable with line highlighting."""
        f1, f2, _, _ = winnowing(self.result_1.content, self.result_2.content)
        return f1, f2

    def highlight_diff(self):
        """Highlight the difference between two Python files."""

        f1, f2 = self.winnowing_wrapper()

        # Wrapper for difference highlight style.
        pre = '<style>.diff_plus { background-color: rgba(0, 255, 0, 0.3) }</style>'

        parsed1 = [pre] + self.result_1.content.split('\n')
        parsed2 = [pre] + self.result_2.content.split('\n')

        for start, end in f1:
            for lin_num in range(start - 1, end):
                parsed1[lin_num] = '<div class={}>{}</div>'.format(
                    'diff_plus', parsed1[lin_num])

        for start, end in f2:
            for lin_num in range(start - 1, end):
                parsed2[lin_num] = '<div class={}>{}</div>'.format(
                    'diff_plus', parsed2[lin_num])        

        for instance in [parsed1, parsed2]:
            for i in range(1, len(instance)):
                if not instance[i].startswith('<div'):
                    instance[i] = '<div>{}</div>'.format(instance[i])

        return parsed1, parsed2
