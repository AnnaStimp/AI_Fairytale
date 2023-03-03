import openai
import json
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
openai.api_key = ""

bd = {}

@app.route("/get-continue-story", methods=["GET"])
def get_continue_story():
    args  = request.args

    print(args)

    if args['id'] not in bd.keys():
        bd[args['id']] = ''

    param = {}
    if len(args['mood']) and len(args['mainCharacter']) and len(args['settingStory']):
        param['mood'] = args['mood']
        param['mainCharacter'] = args['mainCharacter']
        param['settingStory'] = args['settingStory']

    dopDec = ''
    if len(args['decision']):
        bd[args['id']] += '\n\n' + str(args['decision'])
        dopDec = '\n\n' + str(args['decision'])

    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=generate_request(bd[args['id']], args['storyPoint'], param),
            temperature=1,
            max_tokens=500
        )
    except:
        with open('./bd.txt', 'a') as fl:
            fl.write(f"{str(args['id'])}{str(bd[args['id']])}")
        return jsonify({ "ok": False}), 500

    resp = dopDec + str(response.choices[0].text)

    bd[args['id']] += resp

    if resp[-1] !=  '.':
        resp = crop_text(resp)
    print(resp)
    if args['storyPoint'] == 'Continue the story – more dialogues, fewer descriptions of actions. This is a continuation of the story with a plot denouement that will lead to a happy ending.':
        with open('./bd.txt', 'a') as fl:
            fl.write(f"{str(args['id'])}{str(bd[args['id']])}")
    return jsonify({ "ok": True, "new_part": resp })

@app.route("/decisions", methods=["GET"])
def get_story_decisions():
    args  = request.args

    print(args)

    while True:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=generate_dicision(bd[args['id']]),
            temperature=0.8,
            max_tokens=500
        )

        resp = response.choices[0].text
        print(resp)
        
        try:
            res = response_processing(resp)
        except:
            continue
        else:
            break

    return jsonify({ "ok": True, "data": res })

def generate_request(full_story, point, param):
    if len(param.keys()) == 0:
        return f"{full_story} {point}"
    return f"{full_story}\n\nThe mood of the story: {param['mood']}. The main character: {param['mainCharacter']}. Setting of the story: {param['settingStory']}.\n\n{point} The story should be in the format of a dialogue in which the characters and the author of the narrative participate."

def generate_dicision(full_story):
    return f"{full_story}\n\nWrite 3 branches of the story plot and the short name of this branch in the json object format, where the key is the short name of the branch and the value is the text."
        
def response_processing(resp):
    return json.loads(resp.replace('\n', ''))

def crop_text(text):
    text_arr = text.split(".")
    res = ".".join(text_arr[:-1])
    return f'{res}.'

if __name__ == '__main__':
    app.run(debug=True,port=5623)