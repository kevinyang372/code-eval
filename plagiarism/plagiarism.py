from PyInquirer import prompt, Separator
from plagiarism_detection import parse_to_ast, exact_match, unifying_ast_match_wrapper, ast_match_ignoring_variables
from apted_tree_edit_distance import tree_edit_distance
from tokenizer import comment_edit_distance
from winnowing import winnowing


name_to_function = {
    'Exact Match': exact_match,
    'Unifying AST': unifying_ast_match_wrapper,
    'Unifying AST (Ignore Variables)': ast_match_ignoring_variables,
    'Tree Edit Distance': tree_edit_distance,
    'Comment Edit Distance': comment_edit_distance,
    'Winnowing': winnowing
}

questions = [
    {
        'type': 'checkbox',
        'message': 'Select corresponding plagiarism attacks and detection algorithms',
        'name': 'plagiarism',
        'choices': [ 
            Separator('= Plagiarism Attacks ='),
            {
                'name': 'Change Comment'
            },
            {
                'name': 'Change Function Order'
            },
            {
                'name': 'Change Variable Order'
            },
            {
                'name': 'Different'
            },
            {
                'name': 'Rename Variable'
            },
            Separator('= Algorithms ='),
            {
                'name': 'Exact Match'
            },
            {
                'name': 'Unifying AST'
            },
            {
                'name': 'Unifying AST (Ignore Variables)'
            },
            {
                'name': 'Tree Edit Distance'
            },
            {
                'name': 'Winnowing'
            },
            {
                'name': 'Comment Edit Distance'
            }
        ],
        'validate': lambda answer: 'You must choose at least plagiarism attack and one algorithm.'
        if len(answer) == 2 else True
    }
]


def parse_to_filenames(name):
    filename_s = ['test'] + name.lower().split(' ')
    return '_'.join(filename_s) + '.py'


if __name__ == '__main__':
    answers = prompt(questions)

    tree_1 = parse_to_ast('tests/test_original.py')

    functions = []
    files = []

    for ans in answers['plagiarism']:
        if name_to_function.get(ans, None):
            functions.append(ans)
        else:
            files.append(ans)

    for file in files:
        filename = 'tests/' + parse_to_filenames(file)
        tree_2 = parse_to_ast(filename)
        print(f"For {file}")
        print("======================")
        for function in functions:
            print(f"* {function} result:")

            if function == 'Comment Edit Distance':
                print(name_to_function[function]('tests/test_original.py', filename))
            elif function == 'Winnowing':
                _, _, p1, p2 = name_to_function[function]('tests/test_original.py', filename)
                print(f"Original Overlap Percentage: {p1}")
                print(f"Test File Overlap Percentage: {p2}")
            else:
                print(name_to_function[function](tree_1, tree_2))

            print('')
        print('')
