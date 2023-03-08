import openai
import json
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
openai.api_key = ""

db = {}

@app.route("/get-continue-story", methods=["GET"])
def get_continue_story():
    args  = request.args

    if args['id'] not in db.keys() and not len(args['decision']):
        db[args['id']] = [
            {"role": "system", "content": f"""You're a story writer. The mood of the story: {args['mood']}. 
                                            The main character: {args['mainCharacter']}. 
                                            Setting of the story: {args['settingStory']}."""}]

    if args['id'] not in db.keys() and len(args['decision']):
        db[args['id']] = [
            {"role": "system", "content": f"""You're a story writer.
                                            The beginning of the story is as follows: {args['decision']}"""}]
        args['decision'] = ""

    if len(args['decision']):
        db[args['id']].append({"role": "assistant", "content": args['decision']})
    
    db[args['id']].append({"role": "user", "content": args['storyPoint']})

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=db[args['id']],
            temperature=0.8,
            max_tokens=340
        )

        db[args['id']].append(completion.choices[0].message)
    except Exception as e:
        print(e)
        return jsonify({ "ok": False, "error": str(e)}), 500

    resp = args['decision'] + completion.choices[0].message.content

    if resp[-1] !=  '.':
        resp = crop_text(resp)

    
    if 'happy ending' in args['storyPoint']:
        with open('./bd.txt', 'a') as fl:
            story = '\n'.join([i['content'] for i in db[args['id']]])
            fl.write(f"""{args['id']}
                    {story}""" + "\n")

    return jsonify({ "ok": True, "new_part": resp })


@app.route("/decisions", methods=["GET"])
def get_story_decisions():
    args  = request.args

    while True:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=get_decision(db[args['id']]),
            temperature=0.5,
            max_tokens=340
        )
        
        resp = completion.choices[0].message.content
        print(resp)

        try:
            res = response_processing(resp)
            if len(res.keys()) != 3:
                continue
        except Exception as e:
            print(e)
            continue
        else:
            break

    return jsonify({ "ok": True, "data": res })

def response_processing(resp):
    result = {}
    mas = [i for i in resp.split('{')][1:]
    mas = [i.split('}') for i in mas]
    mas = [i[0].replace('\n', '') for i in mas]

    for m in mas:
        c = m.split(':')
        c = [i.split('"') for i in c]
        result[c[0][1]] = c[1][1]

    return json.loads(json.dumps(result))

def get_decision(db):
    return db + [{
        "role": "user", "content": """Come up with three short different story continuations.
Write them to me in json format, where the key is the name of the continuation, and the value is the text.
Output example:
{
'name_story': 'value',
'name_story': 'value',
'name_story': 'value'
}"""
    }]

def crop_text(text):
    text_arr = text.split(".")
    res = ".".join(text_arr[:-1])
    return f'{res}.'

if __name__ == '__main__':
    app.run(debug=True,port=5623)
