import ast
from apted import APTED, Config


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


def copyTree(node, dummy = None):
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
                    copyTree(p, curr)
        elif isinstance(v, ast.AST):
            copyTree(v, curr)

    return curr


def getTreeSize(root):
    return 1 + sum(getTreeSize(node) for node in root.children)


def tree_edit_distance(r1, r2):

    r1, r2 = copyTree(r1), copyTree(r2)
    apted = APTED(r1, r2, CustomConfig())

    return 1 - apted.compute_edit_distance() / max(getTreeSize(r1), getTreeSize(r2))
