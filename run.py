#!/usr/bin/env python
import os
import subprocess

from cert_viewer import configure_app
from cert_viewer.config import get_config
#from flask import (Flask)


def main():
    port = int(os.environ.get('PORT', 5000))
    #conf = get_config()
    #configure_app(conf)
    #db = SQLAlchemy()
    #from alchemy import db
    from cert_viewer import app

    #from cert_viewer import login_manager
    #migrate = Migrate(app, db)
    #from alchemy import Profile
    
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    conf = get_config()    	
    configure_app(conf)  
    app.run('0.0.0.0', port=port, threaded=True)




if __name__ == "__main__":
    main()
