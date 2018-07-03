import logging.config
import os
from flask_login import LoginManager
import gridfs
from flask import (Flask)
from flask_themes2 import (Themes)
from pymongo import MongoClient
from simplekv.fs import FilesystemStore
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask import Flask, request, redirect, url_for
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
UPLOAD_FOLDER = BASE_DIR+"\cert_viewer\static\img"
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

login_manager = LoginManager()

app = Flask(__name__)
Themes(app, app_identifier='cert_viewer')
app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:@localhost/profile'
db = SQLAlchemy(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
login_manager.init_app(app)
migrate = Migrate(app, db)
logging.config.fileConfig(os.path.join(BASE_DIR, 'logging.conf'))
log = logging.getLogger(__name__)
from cert_viewer import alchemy
mongo_connection = None
cert_store = None
intro_store = None

from cert_core.cert_store.certificate_store import CertificateStore, V1AwareCertificateStore
from cert_core.cert_store.gridfs_key_value_store import GridfsKeyValueStore
from cert_viewer.introduction_store_bridge import IntroStore


def configure_app(configuration):
    # Configure data sources
    mongo_client = MongoClient(host=configuration.mongodb_uri)
    conn = mongo_client[
        configuration.mongodb_uri[configuration.mongodb_uri.rfind('/') + 1:len(configuration.mongodb_uri)]]
    global mongo_connection
    mongo_connection = conn

    if configuration.cert_store_type == 'simplekv_fs':
        kv_store = FilesystemStore(configuration.cert_store_path)
        log.info('Configured a file system certificate store with path=%s', configuration.cert_store_path)
    elif configuration.cert_store_type == 'simplekv_gridfs':
        gfs = gridfs.GridFS(conn)
        kv_store = GridfsKeyValueStore(gfs)
        log.info('Configured a gridfs certificate store')

    # Configure verifier
    global cert_store
    if configuration.v1_aware:
        cert_store = V1AwareCertificateStore(kv_store, mongo_connection)
    else:
        cert_store = CertificateStore(kv_store)

    # Configure intro store
    global intro_store
    intro_store = IntroStore(mongo_connection)

    # Configure views
    from cert_viewer import views
    views.add_rules(app, configuration)
