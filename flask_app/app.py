import os

from io import BytesIO

import openai
from flask import Flask, redirect, render_template, request, url_for, flash

from PIL import Image

import requests
import json

import pytesseract

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

openai.api_key = os.getenv("OPENAI_API_KEY")

MATHPIX_APP_ID = os.getenv("MATHPIX_APP_ID")
MATHPIX_API_KEY = os.getenv("MATHPIX_APP_KEY")

'''
mmutableMultiDict([('grade', '10'), 
('topic', 'history'), ('marks', '5'), 
('question', 'What is displacement reaction?'), 
('answer', 'When a more reactive element reacts with a molecule containing less reactive element. It replaces the less reactive element and form the bond with other one, thus displacing the less reactive element')])
'''


@app.route("/", methods=("GET", "POST"))
def index():
    if request.method == "POST":
        print(request.form)
        grade = request.form['grade']
        topic = request.form['topic']
        question = request.form['question']
        answer = request.form['answer']
        total_marks = request.form['marks']

        response = openai.Completion.create(
            model= "text-davinci-003",
            prompt= generate_prompt(grade,topic, question, answer, total_marks),
            temperature=0,
            max_tokens=1000
        )            
        result = response.choices[0].text
        if result:
            result_json = json.loads(result)
            print(result_json)
            marking_scheme = result_json.get('marking_scheme')
            obtained_marks = result_json.get('obtained_marks')
            feedback = result_json.get('feedback')
            return render_template("index.html", question=question, answer=answer, result=result_json, marking_scheme=marking_scheme, obtained_marks=obtained_marks, feedback=feedback)
    return render_template("index.html")


def generate_prompt(grade, topic, question, answer, total_marks):
    return """Evaluate the following answer given here, with the given details.
    Return your analysis in the following json format.
    {
        "marking_scheme": [
            {"name": "field1","full_marks":"full_marks", "obtained_marks": "obtained_marks"},
            {"name": "field2","full_marks":"full_marks", "obtained_marks": "obtained_marks"},
            ...
            {"name": "fieldn","full_marks":"full_marks", "obtained_marks": "obtained_marks"}
        ]
        "obtained_marks": "obtained_marks",
        "feedback": "feedback_text"
    }
    where field1, field2, ... fieldn are the rubric you will use to grade the answer and thier respective marks.

Grade: %s
Topic: %s
Question: %s
Answer: %s
Total_marks: %s
obtained_marks: 
""" % (
        grade, topic, question, answer, total_marks
    )

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def getTextFromImage_MathPix(file, latex=False):
    r = requests.post("https://api.mathpix.com/v3/text",
        files={"file": file},
        data={
        "options_json": json.dumps({
            "math_inline_delimiters": ["$", "$"],
            "rm_spaces": True
        })
        },
        headers={
            "app_id": MATHPIX_APP_ID,
            "app_key": MATHPIX_API_KEY
        }
    )
    r_data = r.json()
    print(json.dumps(r_data, indent=4, sort_keys=True))
    return r_data.get('text')




@app.route("/imgtext", methods=("GET", "POST"))
def imgtext():
    if request.method == 'POST':
        print('sending file')
        f = request.files.get('file')
        print(f.filename)
        if f and allowed_file(f.filename):
            print('sending file 2')
            return getTextFromImage_MathPix(f)
            # img = Image.open(f.stream)
            # text = pytesseract.image_to_string(img)
            # return text
    return ''



# def generate_prompt(animal):
#     return """Suggest three names for an animal that is a superhero.

# Animal: Cat
# Names: Captain Sharpclaw, Agent Fluffball, The Incredible Feline
# Animal: Dog
# Names: Ruff the Protector, Wonder Canine, Sir Barks-a-Lot
# Animal: {}
# Names:""".format(
#         animal.capitalize()
#     )
