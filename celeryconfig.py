import os
import sys
sys.path.insert(0, os.getcwd())

# ## Note: Start worker with -P gevent,
# do not use the CELERYD_POOL option.

BROKER_URL = 'redis://localhost'
CELERY_DISABLE_RATE_LIMITS = True
CELERY_RESULT_BACKEND = 'redis'
CELERY_TASK_RESULT_EXPIRES = 30 * 60

CELERY_IMPORTS = ('tasks', )
