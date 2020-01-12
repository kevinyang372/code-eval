def entry(a, b):
    with open('file.txt', 'w') as file:
        file.write('This is a malicious file')
    return a + b