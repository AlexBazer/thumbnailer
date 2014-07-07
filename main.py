#!/usr/bin/env python2
import json
import errno
from PIL import Image, ImageOps
from celery import group
from celery.result import GroupResult

from flask import Flask, render_template, request, abort, redirect, url_for
import jsonschema
import os
import tasks

MEDIA_ROOT = '/home/cenotop/static/'
THUMBNAILS_DIRECTORY = 'thumbnails/'

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


def ensure_directory_exists(path):
    """
    This function checks for `dirname(path)` to exist,
    and if it is not so creates the directories recursively.

    :note:
        You should pass the full path to the file, which should be stored in the directory.
        If you are passing a path to the directory, be sure to end it with a slash, otherwise not the directory itself
        but it's parent directory will be created.
    """
    try:
        os.makedirs(os.path.dirname(path))
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


app = Flask(__name__)

#@app.route('/')
#def index():
#    return render_template("index.html")

@app.route('/thumbnails/<int:width>/<int:height>/<image>', defaults={'mode': 'fit'})
@app.route('/thumbnails/<int:width>/<int:height>/<image>/<mode>')
def thumbnail(width, height, image, mode):
    image_path = os.path.join(MEDIA_ROOT, image)

    if mode == 'scale':
        thumbnail_path = os.path.join(MEDIA_ROOT, THUMBNAILS_DIRECTORY, str(mode), str(width), str(height), image)
        thumbnail_url = url_for('.thumbnail', **{'image': image, 'width': width, 'height': height, 'mode': mode})
    else:
        thumbnail_path = os.path.join(MEDIA_ROOT, THUMBNAILS_DIRECTORY, str(width), str(height), image)
        thumbnail_url = url_for('.thumbnail', **{'image': image, 'width': width, 'height': height})

    # if settings.DEBUG and os.path.exists(thumbnail_path):
    #     document_root, path = os.path.split(thumbnail_path)
    #     return serve(request, path, document_root=document_root)

    # return 404 if original image doesn't exist
    if not os.path.isfile(image_path):
        abort(404)

    img = Image.open(image_path)

    if img.size[0] > 2 * width or img.size[1] > 2 * height:
        method = Image.ANTIALIAS
    else:
        method = Image.NEAREST

    ensure_directory_exists(thumbnail_path)

    if mode == 'fit':
        thmb = ImageOps.fit(img, (width, height), method)
        thmb.save(thumbnail_path, quality=100, optimize=True, progressive=True)
    elif mode == 'scale':
        img.thumbnail((width, height), method)
        img.save(thumbnail_path, quality=100, optimize=True, progressive=True)

    return redirect(thumbnail_url)

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
    app.run('0.0.0.0')
