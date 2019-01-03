import logging
import os
import re

import bugsnag
from bugsnag.flask import handle_exceptions
from flask import Flask, json
from flask_caching import Cache
from markdown import markdown
from mongoengine import connect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.debug = os.getenv('DEBUG', False)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('PG_URL')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

SITE_ROOT = os.path.dirname(os.path.abspath(__file__))

bugsnag.configure(
    api_key=os.getenv('BUGSNAG_API_KEY'),
    project_root="/app",
    release_stage=os.getenv('STAGE', 'development'),
    notify_release_stages=["production"]
)
handle_exceptions(app)

logging.basicConfig(level=logging.INFO)

# Cache settings
cache_type = 'null' if app.debug else 'redis'
cache = Cache(app, config={'CACHE_TYPE': cache_type, 'CACHE_REDIS_HOST': 'redis'})

# Set connect to False for pre-forking to work
connect(db='clashstats', host=os.getenv('DB_HOST'), connect=False)

import clashleaders.views  # noqa

MANIFEST_FILE = os.path.join(SITE_ROOT, "static", "manifest.json")


def manifest_path(file):
    with open(MANIFEST_FILE) as f:
        data = json.load(f)
    return data[file]


def inline_path(file):
    path = os.path.join(SITE_ROOT, manifest_path(file).lstrip('/'))
    with open(path) as f:
        content = f.read()
        return re.sub(r'^//# sourceMappingURL=.*$', '', content, flags=re.MULTILINE)


def first(list, i): return list[:i]


app.add_template_global(manifest_path, 'manifest_path')
app.add_template_global(inline_path, 'inline_path')
app.add_template_filter(markdown, 'markdown')
app.add_template_filter(first, 'first')
