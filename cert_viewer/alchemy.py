from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
#from cert_viewer import login_manager
#app=Flask(__name__)
from cert_viewer import db,login_manager

#db=SQLAlchemy(app)
#from cert_viewer import login_manager
class Profile(UserMixin,db.Model):
	__tablename__='profile'
	id = db.Column(db.Integer, primary_key=True)
	user = db.Column(db.String(100))
	password=db.Column(db.String(100))
	name=db.Column(db.String(200))
	issuer_url = db.Column(db.String(200),nullable=False, default="")
	issuer_email = db.Column(nullable=False, default="")
	issuer_id = db.Column( db.String(200),nullable=False, default="")
	revocation_list = db.Column(db.String(200),nullable=False, default="")
	issuer_public_key = db.Column(db.String(128), nullable=False, default="")
	certificate_description = db.Column(nullable=False, default="")
	certificate_title = db.Column(db.String(200), nullable=False, default="")
	criteria_narrative = db.Column(nullable=False,default="")
	badge_id = db.Column(db.String(32), default="")
	issuer_logo_file = db.Column(nullable=False,default="")
	cert_image_file = db.Column(nullable=False, default="")
	issuer_signature_file = db.Column(nullable=False,default="")

	'''def __init__(self,user,issuer_url,issuer_email,issuer_id,revocation_list,issuer_public_key,certificate_description,certificate_title,criteria_narrative,badge_id,issuer_logo_file,cert_image_file,issuer_signature_file):
	        self.user=user
	        self.issuer_url=issuer_url
	        self.issuer_email=issuer_email
	        self.issuer_id=issuer_id
	        self.revocation_list=revocation_list
	        self.issuer_public_key=issuer_public_key
	        self.certificate_description=certificate_description
	        self.certificate_title=certificate_title
	        self.criteria_narrative=criteria_narrative
	        self.badge_id=badge_id
	        self.issuer_logo_file=issuer_logo_file
	        self.cert_image_file=cert_image_file
	        self.issuer_signature_file=issuer_signature_file
	def is_authenticated(self):
		return True
	def is_active(self):
		return True
	def is_anonymous(self):
		return False
	def get_id(self):
		return unicode(self.user)'''
	
	def __repr__(self):
        	return self.user
@login_manager.user_loader
def load_user(user_id):
    	return Profile.query.get(int(user_id))