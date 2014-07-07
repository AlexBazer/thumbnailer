import urllib

from celery import task
import os


@task
def download_image(url, path):
    try:
        if os.path.isfile(path):
            return "EXISTS"
        urllib.urlretrieve(url, path)
    except Exception as exc:
        return "ERROR"
    return "SUCCESS"

