import logging
import os
import datetime
import json
import pdb
from os import listdir
from os.path import isfile, join
from flask import jsonify, redirect
from flask_themes2 import render_theme_template, static_file_url
from werkzeug.routing import BaseConverter
from flask import Flask, render_template, request, redirect, url_for, abort, session,flash
from cert_viewer import certificate_store_bridge
from cert_viewer import introduction_store_bridge
from cert_viewer import verifier_bridge
from cert_viewer import certificate_formatter
from cert_viewer.forms import LoginForm,RegistrationForm,ProfileForm,LogoUpload,IssuerForm,IdentityForm
#from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from cert_viewer.alchemy import  Profile
from cert_viewer import db
from flask_login import login_required, login_user, logout_user
from cert_viewer import ALLOWED_EXTENSIONS
DEFAULT_THEME = 'default'
from flask import send_from_directory
from werkzeug.utils import secure_filename
from Naked.toolshed.shell import execute_js, muterun_js
import json

def update_app_config(app, config):
    app.config.update(
        SECRET_KEY=config.secret_key,
        ISSUER_NAME=config.issuer_name,
        SITE_DESCRIPTION=config.site_description,
        ISSUER_LOGO_PATH=config.issuer_logo_path,
        ISSUER_EMAIL=config.issuer_email,
        THEME=config.theme,
    )
    print(config.theme)
    recent_certs = update_recent_certs()
    app.config['RECENT_CERT_IDS'] = recent_certs[-10:]

def update_recent_certs():
    cert_path = "cert_data"
    certs_folder = []
    for file in listdir(cert_path):
        if file[len(file) - 4:] == "json":
            certs_folder.append(file[:len(file) - 5])
    
    return certs_folder

def render(template, **context):
    from cert_viewer import app
    return render_theme_template(app.config['THEME'], template, **context)


def configure_views(app, config):
    update_app_config(app, config)
    add_rules(app, config)


from flask.views import View


class GenericView(View):
    def __init__(self, template):
        self.template = template

        super(GenericView, self).__init__()

    def dispatch_request(self):
        return render(self.template)
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def add_rules(app,config):
    from cert_viewer.views.award_view import AwardView
    from cert_viewer.views.json_award_view import JsonAwardView
    from cert_viewer.views.renderable_view import RenderableView
    from cert_viewer.views.issuer_view import IssuerView
    from cert_viewer.views.verify_view import VerifyView
    from cert_viewer.views.request_view import RequestView
    

    update_app_config(app, config)
    app.url_map.converters['regex'] = RegexConverter

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        """
        Handle requests to the /register route
        Add an employee to the database through the registration form
        """
        form = RegistrationForm()
        if form.validate_on_submit():
            p = Profile(user=form.username.data,                                
                                issuer_email=form.email.data,                                
                                password=form.password.data)

            # add employee to the database
            db.session.add(p)
            db.session.commit()
            import csv
            fileName="cert_viewer\\rosters"+p.user+".csv"
            o=["name","pubkey","identity"]
            csv.register_dialect('myDialect',quoting=csv.QUOTE_ALL,skipinitialspace=True)
            with open(fileName, 'w') as f:
                writer = csv.writer(f, dialect='myDialect')
                writer.writerow(o)
            f.close()
            flash('You have successfully registered! You may now login.')

            # redirect to the login page
            return redirect('/')

        # load registration template
        return render_template('/signup.html', form=form)

    @app.route('/autocomplete', methods=['GET'])
    def autocomplete():
        search = request.args.get('q')
        query = Profile.query.filter(Profile.name.like('%' + str(search) + '%'))
        results = [mv[0] for mv in query.all()]
        return jsonify(matching_results=results)

    @app.route('/')
    def home():         
        return render_template('base.html')

    @app.route('/login',methods=['GET', 'POST'])
    def login():
        form = LoginForm(request.form)
        if request.method == 'POST' and form.validate():
            p=Profile.query.filter_by(user=form.username.data,password=form.password.data)
            if p.count()==1:
                p=p.first()
                login_user(p)
                session['user']=p.user
                flash('Login Successsful')
                return redirect('/profile')
            return render_template('/login.html',form=form)
        return render_template('/login.html',form=form) 

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)            
    @app.route('/logout')
    @login_required
    def logout():
        """
        Handle requests to the /logout route
        Log an employee out through the logout link
        """
        logout_user()
        session.pop('user',None)
        flash('You have successfully been logged out.')

        # redirect to the login page
        return redirect('/')   
                
       
    @app.route('/profile')
    @login_required
    def profile():
        return render_template('profile.html')
    @app.route('/logo',methods=['GET', 'POST'])
    @login_required
    def logo():
        p=Profile.query.filter_by(user=session['user']).first()
        #form=LogoUpload(request.form)

        if request.method == 'POST':
            # check if the post request has the file part
            if 'file' not in request.files:
                
                flash('No file part')
                return redirect('/logo')
            file = request.files['file']
            # if user does not select file, browser also
            # submit a empty part without filename
            if file.filename == '':
                
                flash('No selected file')
                return redirect('/logo')
            if file and allowed_file(file.filename):
                
                filename = secure_filename(file.filename)
                parts=filename.split('.')
                timestamp=str(datetime.datetime.now())
                timestamp=timestamp.replace(" ","")
                timestamp=timestamp.replace(".","")

                filename=parts[0]+timestamp.replace(":","")+'.'+parts[1]
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                p.issuer_logo_file='/static/img/'+filename
                db.session.commit()
                return redirect('/cert_image')
        return render_template('logo.html')
    @app.route('/cert_image',methods=['GET', 'POST'])
    @login_required
    def cert_image():
        p=Profile.query.filter_by(user=session['user']).first()
        #form=LogoUpload(request.form)

        if request.method == 'POST':
            # check if the post request has the file part
            if 'file' not in request.files:
                
                flash('No file part')
                return redirect('/cert_image')
            file = request.files['file']
            # if user does not select file, browser also
            # submit a empty part without filename
            if file.filename == '':
                
                flash('No selected file')
                return redirect('/cert_image')
            if file and allowed_file(file.filename):
                
                filename = secure_filename(file.filename)
                parts=filename.split('.')
                timestamp=str(datetime.datetime.now())
                timestamp=timestamp.replace(" ","")
                timestamp=timestamp.replace(".","")

                filename=parts[0]+timestamp.replace(":","")+'.'+parts[1]
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                p.cert_image_file='/static/img/'+filename
                db.session.commit()
                return redirect('/signature')
        return render_template('cert_image.html')
    @app.route('/signature',methods=['GET', 'POST'])
    @login_required
    def signature():
        p=Profile.query.filter_by(user=session['user']).first()
        #form=LogoUpload(request.form)

        if request.method == 'POST':
            # check if the post request has the file part
            if 'file' not in request.files:
                
                flash('No file part')
                return redirect('/signature')
            file = request.files['file']
            # if user does not select file, browser also
            # submit a empty part without filename
            if file.filename == '':
                
                flash('No selected file')
                return redirect('/signature')
            if file and allowed_file(file.filename):
                
                filename = secure_filename(file.filename)
                parts=filename.split('.')
                timestamp=str(datetime.datetime.now())
                timestamp=timestamp.replace(" ","")
                timestamp=timestamp.replace(".","")
                #timestamp=timestamp.replace(" ","")
                filename=parts[0]+timestamp.replace(":","")+'.'+parts[1]
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                p.issuer_signature_file='/static/img/'+filename
                db.session.commit()
                return redirect('/deploy')
        return render_template('signature.html')

    @app.route('/updateProfile',methods=['GET', 'POST'])
    @login_required
    def profile_update():
        p=Profile.query.filter_by(user=session['user']).first()
        form = ProfileForm(request.form)
                    
               
        if form.validate_on_submit():                    

            
            p.name=form.name.data                                
            p.issuer_url=form.issuer_url.data,
            p.issuer_id=form.issuer_id.data,
            p.revocation_list=form.revocation_list.data,                                
            p.issuer_public_key=form.issuer_public_key.data,
            p.certificate_description=form.certificate_description.data,
            p.certificate_title=form.certificate_title.data,
            p.criteria_narrative=form.criteria_narrative.data,
            p.badge_id=form.badge_id.data,
            #p.issuer_logo_file=form.issuer_logo_file.data,
            p.cert_image_file=form.cert_image_file.data,
            p.issuer_signature_file=form.issuer_signature_file.data

            # add employee to the database
            #db.session.update(p)
            db.session.commit()
            flash('You have successfully registered! You may now login.')

            # redirect to the login page
            return redirect('/logo')
        else:
            file_url = None
            form.name.data=p.name
            form.issuer_url.data=p.issuer_url
            form.issuer_id.data=p.issuer_id
            form.revocation_list.data=p.revocation_list
            form.issuer_public_key.data=p.issuer_public_key
            form.certificate_description.data=p.certificate_description
            form.certificate_title.data=p.certificate_title
            form.criteria_narrative.data=p.criteria_narrative
            form.badge_id.data=p.badge_id
            #form.issuer_logo_file.data=p.issuer_logo_file
            form.cert_image_file.data=p.cert_image_file
            form.issuer_signature_file.data=p.issuer_signature_file

        # load registration template
        
        return render_template('profileUpdate.html',form=form)
    @app.route('/deploy',methods=['GET', 'POST'])
    @login_required
    def deploy():
        p=Profile.query.filter_by(user=session['user']).first()
        form=IdentityForm(request.form)
        if form.validate_on_submit():
            #from cert_viewer.cert_tools.cert_tools import create_v2_issuer
            import subprocess
            pubkey=p.issuer_public_key
            logopath=p.issuer_logo_file
            logopath=logopath.replace("/","\\")
            logopath=logopath[1:]
            print(logopath)
            path=os.path.join(os.getcwd(),'cert_tools/conf.ini')         
            script=['python',"create_v2_issuer.py",'-c',path,'-k',pubkey,'-r',"To be updated",'-d',"akjbf",'--data_dir',"cert_viewer",'-m',logopath,'-o',p.user+".json"]
            status=subprocess.call(script,shell=True)
            print("status:",status)
            if not status:
                with open(p.user+".json") as f:
                    data = json.load(f)
                path=os.path.join(os.getcwd(),'cert_viewer/static/js/store.js')
                response = muterun_js(path,p.user)
                print("response:",response.stdout)
                if response.exitcode==0:
                    hash_value=response.stdout
                    p.issuer_id=hash_value.decode("UTF-8")
                    db.session.commit()
                    return redirect('/profile')
                else:
                    return response.stderr.decode("utf-8")
                
            return render_template('issuer.html',form=form)
            
        return render_template('issuer.html',form=form)

    @app.route('/issue_certs',methods=['GET', 'POST'])
    @login_required

    def issue_certs():
        form=IssuerForm(request.form)
        p=Profile.query.filter_by(user=session['user']).first()        
        if form.validate_on_submit():
            import subprocess
            pubkey=p.issuer_public_key
            logopath=p.issuer_logo_file
            logopath=logopath.replace("/","\\")
            logopath=logopath[1:]
            print(logopath)
            imagepath=p.cert_image_file
            imagepath=imagepath.replace("/","\\")
            imagepath=imagepath[1:]
            print(imagepath)
            signaturepath=p.issuer_signature_file
            signaturepath=signaturepath.replace("/","\\")
            signaturepath=signaturepath[1:]
            print(signaturepath)
            path=os.path.join(os.getcwd(),'cert_tools/conf.ini')         
            script=['python',"create_v2_certificate_template.py",'-c',path,'--issuer_public_key',pubkey,'-r',"To be updated",'-d',"akjbf",'--data_dir',"cert_viewer",'--issuer_logo_file',logopath,'--cert_image_file',imagepath,'--issuer_signature_file',signaturepath,'--issuer_url',"https://www.ioe.edu.np",'--issuer_name',p.name,'--issuer_id',p.issuer_id,'--issuer_key',"pqrst",'--certificate_title',"Certificate of Achievement",'--criteria_narrative',p.criteria_narrative,'--badge_id',p.badge_id,'--issuer_signature_lines',"Signature of TU"]
            status1=subprocess.call(script,shell=True)
            print("status1:",status1)
            if not status1:
                path=os.path.join(os.getcwd(),'cert_tools/conf.ini')
                script=['python',"instantiate_v2_certificate_batch.py",'-c',path,'--data_dir',"cert_viewer",'--roster',"rosters\\"+p.user+".csv",'--no-clobber','False']
                status2=subprocess.call(script,shell=True)
                if not status2:
                    script=['python',"cert_issuer/__main__.py",'--issuing_address',p.issuer_public_key,'--usb_name',"G:",'--key_file',"private.txt",'--chain',"ethereum_ropsten"]
                    status3=subprocess.call(script,shell=True)
                    if not status3:
                        return redirect('/profile')
                    return "Issuing failed but certificates created successfully"
                return "Error in instantiating"
            return render_template("cert_issuer.html",form=form)
        return render_template("cert_issuer.html",form=form)





    @app.route('/issuer/<specific>')
    def issuer(specific):
        conf = get_config(specific)     
        configure_app(conf)     
        #session['issuer']=True     
        return redirect("/index", code=302)


    app.add_url_rule('/index', view_func=GenericView.as_view('index', template='index.html'))
    #app.add_url_rule('/', view_func=GenericView.as_view('index', template='index.html'))     
    #app.add_url_rule('/', view_func=GenericView.as_view('base', template="base.html"))
    
    app.add_url_rule(rule='/<certificate_uid>', endpoint='award',
                     view_func=AwardView.as_view(name='award', template='award.html',
                     view=certificate_store_bridge.award))

    app.add_url_rule('/certificate/<certificate_uid>',
                     view_func=JsonAwardView.as_view('certificate', view=certificate_store_bridge.get_award_json))

    app.add_url_rule('/verify/<certificate_uid>',
                     view_func=VerifyView.as_view('verify', view=verifier_bridge.verify))

    app.add_url_rule('/intro/', view_func=introduction_store_bridge.insert_introduction, methods=['POST', ])
    app.add_url_rule('/request', view_func=RequestView.as_view(name='request'))
    app.add_url_rule('/faq', view_func=GenericView.as_view('faq', template='faq.html'))
    app.add_url_rule('/ethkeys', view_func=GenericView.as_view('ethkeys', template='ethkeys.html'))
    #app.add_url_rule('/issuer/<issuer_file>', view_func=IssuerView.as_view('issuer',view=certificate_formatter.get_formatted_award_and_verification_info))
    #app.add_url_rule('/issuer/<issuer_file>', view_func=issuer_page)
    #app.add_url_rule('/issuer/', view_func=issuer_page)
    app.add_url_rule('/spec', view_func=spec)
    
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(KeyError, key_error)
    app.register_error_handler(500, internal_server_error)
    app.register_error_handler(Exception, unhandled_exception)


from flasgger import Swagger

def spec():
    from cert_viewer import app

    return jsonify(Swagger(app))


def issuer_page():
    from cert_viewer import app
    #the_url = static_file_url(theme=app.config['THEME'], filename = (os.path.join('issuer/', issuer_file)))
    return redirect("/", code=302)



class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


# Errors
def page_not_found(error):
    logging.error('Page not found: %s', error, exc_info=True)
    return 'This page does not exist', 404


def key_error(error):
    key = error.args[0]
    logging.error('Key not found not found: %s, error: ', key)

    message = 'Key not found: ' + key
    return message, 404

def internal_server_error(error):
    logging.error('Server Error: %s', error, exc_info=True)
    return 'Server error: {0}'.format(error), 500


def unhandled_exception(e):
    logging.exception('Unhandled Exception: %s', e, exc_info=True)
    return 'Unhandled exception: {0}'.format(e), 500
