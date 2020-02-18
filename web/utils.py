from web import app
import os

def read_file(file, filename):
    file.save(os.path.join(app.config["FILE_UPLOADS"], filename))

    content = []
    with open(os.path.join(app.config["FILE_UPLOADS"], filename), 'r') as file:
        for line in file:
            content.append(line)
    
    os.remove(os.path.join(app.config["FILE_UPLOADS"], filename))
    return ''.join(content)