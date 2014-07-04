import urllib

from celery import task

@task
def download_image(url, path):
    try:
        urllib.urlretrieve(url, path)
    except Exception as exc:
        return "ERROR"
    return "SUCCESS"

