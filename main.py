#!/usr/bin/env python2
import json
from celery import group
from celery.result import GroupResult

from flask import Flask, render_template, request
import jsonschema
import tasks

URLS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",

    "type": "object",
    "description": "schema for an urls list",
    "required": ["urls"],
    "properties": {
        "urls": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "path": {"type": "string"}
                },
                "required": ["url", "path"]
            },
            "uniqueItems": True
        }
    }
}

app = Flask(__name__)

#@app.route('/')
#def index():
#    return render_template("index.html")


@app.route('/api/status/<group_id>')
def status(group_id):
    result = GroupResult.restore(group_id)
    if not result:
        return json.dumps({
            'error': 'Does not exist'
        })

    return json.dumps({
        'tasks': [
            {
                'id': task.id,
                'status': task.status,
                'ready': task.ready(),
                'result': task.result
            } for task in result.children
        ],
        'ready': result.ready(),
        'completed': result.completed_count()
    })


@app.route('/api/add_tasks', methods=['POST'])
def add_tasks():
    try:
        data = json.loads(request.form.get('data', ''))
    except ValueError:
        return json.dumps({
            'error': 'Parsing error'
        })

    try:
        jsonschema.validate(data, URLS_SCHEMA)
    except jsonschema.ValidationError as e:
        return json.dumps({
            'error': 'Validation error',
            'message': e.message
        })

    result = group([
        tasks.download_image.s(item['url'], item['path']) for item in data['urls']
    ]).apply_async()
    result.save()

    return json.dumps({
        'group_id': result.id
    })

if __name__ == '__main__':
    app.debug = True
    app.run()
