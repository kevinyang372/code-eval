import ast
import itertools

with open("similar_code1.py", "r") as source:
    tree1 = ast.parse(source.read())

with open("similar_code2.py", "r") as source:
    tree2 = ast.parse(source.read())

mapping = {}

# Exact match between two pieces of code
def exact_match(node1, node2):
    if type(node1) is not type(node2):
        return False
    if isinstance(node1, ast.AST):
        for k, v in vars(node1).items():
            if k in ('lineno', 'col_offset', 'ctx'):
                continue
            if not exact_match(v, getattr(node2, k)):
                return False

        return True
    elif isinstance(node1, list):
        return all(itertools.starmap(exact_match, zip(node1, node2)))
    else:
        return node1 == node2


# unifying ast match detecting naive variable renaming
def unifying_ast_match(node1, node2):
    if type(node1) is not type(node2):
        return False
    if isinstance(node1, ast.AST):
        for k, v in vars(node1).items():
            if k in ('lineno', 'col_offset', 'ctx'):
                continue

            if (k == 'id' or k == 'arg') and v != getattr(node2, k):
                if v not in mapping:
                    mapping[v] = getattr(node2, k)
                elif mapping[v] != getattr(node2, k):
                    return False
            elif not unifying_ast_match(v, getattr(node2, k)):
                return False

        return True
    elif isinstance(node1, list):
        return all(itertools.starmap(unifying_ast_match, zip(node1, node2)))
    else:
        return node1 == node2


# ignore variables
def ast_match_ignoring_variables(node1, node2):
    if type(node1) is not type(node2):
        return False
    if isinstance(node1, ast.AST):
        for k, v in vars(node1).items():
            if k in ('lineno', 'col_offset', 'ctx', 'id', 'arg'):
                continue
            elif not ast_match_ignoring_variables(v, getattr(node2, k)):
                return False

        return True
    elif isinstance(node1, list):
        return all(itertools.starmap(ast_match_ignoring_variables, zip(node1, node2)))
    else:
        return node1 == node2


def traverse(node):
    for k, v in vars(node).items():
        print(k, v)
        if isinstance(v, list):
            for p in v:
                if isinstance(p, ast.AST):
                    traverse(p)
        elif isinstance(v, ast.AST):
            traverse(v)



print(exact_match(tree1, tree2))
print(unifying_ast_match(tree1, tree2))
print(ast_match_ignoring_variables(tree1, tree2))