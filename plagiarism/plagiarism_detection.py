import ast
import itertools
import collections

with open("similar_code1.py", "r") as source:
    tree1 = ast.parse(source.read())

with open("similar_code2.py", "r") as source:
    tree2 = ast.parse(source.read())

mapping = {}

# Exact match between two pieces of code
def exact_match(node1, node2):
    if type(node1) is not type(node2):
        return 0
    if isinstance(node1, ast.AST):
        for k, v in vars(node1).items():
            if k in ('lineno', 'col_offset', 'ctx'):
                continue
            if not exact_match(v, getattr(node2, k)):
                return 0

        return 1
    elif isinstance(node1, list):
        return sum(itertools.starmap(exact_match, zip(node1, node2))) / float(len(node1))
    else:
        return 1 if node1 == node2 else 0


# unifying ast match detecting naive variable renaming
def unifying_ast_match(node1, node2):
    if type(node1) is not type(node2):
        return 0
    if isinstance(node1, ast.AST):
        for k, v in vars(node1).items():
            if k in ('lineno', 'col_offset', 'ctx'):
                continue

            if (k == 'id' or k == 'arg') and v != getattr(node2, k):
                if v not in mapping:
                    mapping[v] = getattr(node2, k)
                elif mapping[v] != getattr(node2, k):
                    return 0
            elif not unifying_ast_match(v, getattr(node2, k)):
                return 0

        return 1
    elif isinstance(node1, list):
        return sum(itertools.starmap(unifying_ast_match, zip(node1, node2))) / float(len(node1))
    else:
        return 1 if node1 == node2 else 0


# ignore variables
d = collections.defaultdict(set)
def ast_match_ignoring_variables(node1, node2):
    if type(node1) is not type(node2):
        return False
    if isinstance(node1, ast.AST):
        for k, v in vars(node1).items():
            if k in ('lineno', 'col_offset', 'ctx', 'id', 'arg'):
                continue
            elif not ast_match_ignoring_variables(v, getattr(node2, k)):
                return False

        if 'lineno' in vars(node1):
            if 'end_lineno' in vars(node1):
                d[getattr(node1, 'lineno'), getattr(node1, 'end_lineno')] = getattr(node2, 'lineno'), getattr(node2, 'end_lineno')
            else:
                d[getattr(node1, 'lineno'), getattr(node1, 'lineno')] = getattr(node2, 'lineno'), getattr(node2, 'lineno')

        return True
    elif isinstance(node1, list):
        return all(itertools.starmap(ast_match_ignoring_variables, zip(node1, node2)))
    else:
        return node1 == node2


# reordering
def ast_match_reordering(node1, node2, is_parent = True):
    if type(node1) is not type(node2):
        return False
    if isinstance(node1, ast.AST):

        next_parent = is_parent and 'lineno' not in vars(node1)

        for k, v in vars(node1).items():
            if k in ('lineno', 'col_offset', 'ctx', 'id', 'arg', 'name'):
                continue
            elif not ast_match_reordering(v, getattr(node2, k), next_parent):
                return False

        if 'lineno' in vars(node1) and is_parent:
            if 'end_lineno' in vars(node1):
                d[getattr(node1, 'lineno'), getattr(node1, 'end_lineno')].add((getattr(node2, 'lineno'), getattr(node2, 'end_lineno')))
            else:
                d[getattr(node1, 'lineno'), getattr(node1, 'lineno')].add((getattr(node2, 'lineno'), getattr(node2, 'lineno')))

        return True
    elif isinstance(node1, list):
        if len(node1) <= len(node2):
            for n1 in node1:
                f = False
                for n2 in node2:
                    if ast_match_reordering(n1, n2): f = True
                
                if not f: return  False

            return True

        else:
            for n2 in node2:
                f = False
                for n1 in node1:
                    if ast_match_reordering(n1, n2): f = True
                
                if not f: return False

            return True
    else:
        return node1 == node2


def traverse(node, level = 0):
    print(type(node).__name__)
    for k, v in vars(node).items():
        if isinstance(v, list):
            for p in v:
                if isinstance(p, ast.AST):
                    traverse(p, level + 1)
        elif isinstance(v, ast.AST):
            traverse(v, level + 1)


print(exact_match(tree1, tree2))
print(unifying_ast_match(tree1, tree2))
# print(ast_match_ignoring_variables(tree1, tree2))
print(ast_match_reordering(tree1, tree2))
print(d)

from zss import simple_distance, Node

def copyTree(node, dummy):
    t = type(node).__name__

    if 'name' in node._fields:
        t += ':' + node.name
    elif 'id' in node._fields:
        t += ':' + node.id
    
    curr = Node(t)
    if dummy is not None: dummy.addkid(curr)

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


A = (copyTree(tree1, None))
B = (copyTree(tree2, None))
print(getTreeSize(A))
print(getTreeSize(B))
print(simple_distance(A, B))
