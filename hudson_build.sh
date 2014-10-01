#!/bin/sh

export WORKON_HOME=~/.virtualenvs/
. /usr/local/bin/virtualenvwrapper.sh

workon redakcja
pip install -r requirements.txt
pip install -r requirements-test.txt
django-admin.py test --settings=redakcja.settings.test
