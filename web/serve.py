from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import importlib

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["FILE_UPLOADS"] = "/Users/kevin/desktop/Github/codeEval/web/tmp"
app.config["ALLOWED_EXTENSIONS"] = ["py", "ipynb"]
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))

db.create_all()
example_user = User(name="Philip Sterne")
db.session.merge(example_user)
db.session.commit()

@app.route('/', methods=["GET", "POST"])
def index():

    def is_valid(filename):
        if filename and '.' in filename and filename.split('.')[1] in app.config["ALLOWED_EXTENSIONS"]:
            return True
        return False

    if request.method == "POST":
        if request.files:
            file = request.files["code"]

            if is_valid(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["FILE_UPLOADS"], filename))

                test_cases = importlib.import_module('.sample_test', 'web.tests')
                to_test = importlib.import_module('.' + filename.split('.')[0], 'web.tmp')

                res = test_cases.TestCases(to_test.add).test()
                print(res)

                os.remove(os.path.join(app.config["FILE_UPLOADS"], filename))

            return redirect(request.url)

    return render_template('index.html')

@app.route('/users')
def users():
    users = User.query.all()
    return render_template('users.html', users=users)

if __name__ == '__main__':
    app.run()
