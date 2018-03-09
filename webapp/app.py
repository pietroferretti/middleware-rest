#!/usr/bin/env/python3

# from teacher import *
# from parent import *
# from admin import *

# import json

from flask import Flask
from flask import request
app = Flask(__name__)


def show_teachers():
    return []

def create_teacher():
    return True


@app.route('/')
def show_root():
    # hypermedia qui?
    return 'Hello, World!'

@app.route('/teacher', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        show_teachers()
    else:
        create_teacher()