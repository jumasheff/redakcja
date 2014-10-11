from fnpdjango.deploy import *
try:
    from fabfile_local import *
except ImportError:
    pass


@task
def staging():
    env.hosts = ['54.77.63.92']
    env.user = 'dastan'
    env.app_path = '/home/dastan/redakcja'
    env.project_name = 'redakcja'
    env.services = [
        DebianGunicorn('redakcja'),
    ]
