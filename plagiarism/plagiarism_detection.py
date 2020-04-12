import ast
import itertools

with open("similar_code1.py", "r") as source:
    tree1 = ast.parse(source.read())

with open("similar_code2.py", "r") as source:
    tree2 = ast.parse(source.read())


def ast_match(node1, node2):
    if type(node1) is not type(node2):
        return False
    if isinstance(node1, ast.AST):
        for k, v in vars(node1).items():
            if k in ('lineno', 'col_offset', 'ctx'):
                continue
            if not ast_match(v, getattr(node2, k)):
                return False
        return True
    elif isinstance(node1, list):
        return all(itertools.starmap(ast_match, zip(node1, node2)))
    else:
        return node1 == node2

print(ast_match(tree1, tree2))