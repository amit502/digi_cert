import sys
from flask_wtf import FlaskForm
from wtforms import Form, TextAreaField, validators, RadioField, StringField,PasswordField,FormField,SubmitField
from wtforms.validators import DataRequired, Email, EqualTo,ValidationError
from flask_wtf.file import FileField,FileRequired,FileAllowed
from cert_viewer.alchemy import Profile
from flask import session


def get_coerce_val():
    if sys.version_info.major < 3:
        coerce_val = unicode
    else:
        coerce_val = str
    return coerce_val


class BitcoinForm(Form):
    identity = RadioField('Identity', choices=[
        ('yes', 'Yes, I have an Ethereum identity'),
        ('no', 'No, I don\'t have an Ethereum identity')], coerce=get_coerce_val())
class RegistrationForm(FlaskForm):
    """
    Form for users to create new account
    """
    
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
                                        DataRequired(),
                                        EqualTo('confirm_password')
                                        ])
    confirm_password = PasswordField('Confirm Password')
    #submit = SubmitField('Register')

    def validate_email(self, field):
        if Profile.query.filter_by(issuer_email=field.data).first():
            raise ValidationError('Email is already in use.')

    def validate_username(self, field):
        if Profile.query.filter_by(user=field.data).first():
            raise ValidationError('Username is already in use.')

class LogoUpload(FlaskForm):
    issuer_logo_file = FileField('Logo File')
    upload=SubmitField('Upload')

class IdentityForm(FlaskForm):
    host=SubmitField('Deploy on IPFS')
class IssuerForm(FlaskForm):
    issued=SubmitField('Issue Certificate Batch')    


class ProfileForm(FlaskForm):
    """
    Form for users to create new account
    """
    name = StringField('Name:', validators=[DataRequired()])
    issuer_url = StringField('URL:', validators=[DataRequired()])
    issuer_id = StringField('ID:', validators=[DataRequired()])
    revocation_list = StringField('Revocation List:', validators=[DataRequired()])
    issuer_public_key = StringField('Public Key:', validators=[DataRequired()])
    certificate_description=TextAreaField('Certificate Description:', validators=[DataRequired()])
    certificate_title = StringField('Certificate Title:', validators=[DataRequired()])
    criteria_narrative = TextAreaField('Criteria Narrative:', validators=[DataRequired()])
    badge_id = StringField('Badge ID:', validators=[DataRequired()])
    #issuer_logo_file = StringField('Logo File:', validators=[DataRequired()])
    cert_image_file = StringField('Certificate Image:', validators=[DataRequired()])
    issuer_signature_file = StringField('Signature File:', validators=[DataRequired()])

    
    #submit = SubmitField('Register')

 
class AdminForm(FlaskForm):
    username = StringField(
        'username', [
            validators.required(), validators.length(
                max=200)])
    password = PasswordField(
        'password', [
            validators.required()])
    ipfs_hash=StringField(
        'ipfs_hash', [
            validators.required(), validators.length(
                max=200)])
class LoginForm(Form):
    username = StringField(
        'username', [
            validators.required(), validators.length(
                max=200)])
    password = PasswordField(
        'password', [
            validators.required()])

class EditForm(FlaskForm):
    name = StringField(
        'Name', [
            validators.required(), validators.length(
                max=200)])
    
    email = StringField(
        'Email', [
            validators.required(), validators.length(
                max=200)])
    pubkey = StringField(
        'Ethereum Public Address', [
            validators.required(), validators.length(
                max=63)])
    
class SimpleRegistrationForm(Form):
    first_name = StringField(
        'First Name', [
            validators.required(), validators.length(
                max=200)])
    last_name = StringField(
        'Last Name', [
            validators.required(), validators.length(
                max=200)])
    email = StringField(
        'Email', [
            validators.required(), validators.length(
                max=200)])
    pubkey = StringField(
        'Ethereum Public Address', [
            validators.required(), validators.length(
                max=42)])

    def to_user_data(self):
        user_data = {
            'ethereumAddress': self.pubkey.data,
            'email': self.email.data,
            'firstName': self.first_name.data,
            'lastName': self.last_name.data
        }
        return user_data


class ExtendedRegistrationForm(Form):
    """Example of a registration form with additional fields. Corresponds to request_extended.html."""
    first_name = StringField(
        'First Name', [
            validators.required(), validators.length(
                max=200)])
    last_name = StringField(
        'Last Name', [
            validators.required(), validators.length(
                max=200)])
    email = StringField(
        'Email', [
            validators.required(), validators.length(
                max=200)])
    pubkey = StringField(
        'Bitcoin Public Address', [
            validators.required(), validators.length(
                max=35)])

    address = StringField(
        'Mailing Address', [
            validators.required(), validators.length(
                max=200)])
    city = StringField(
        'City', [
            validators.required(), validators.length(
                max=200)])
    state = StringField('State/Province/Region',
                        [validators.required(), validators.length(max=200)])
    zipcode = StringField('ZIP/Postal Code',
                          [validators.required(),
                           validators.length(max=200)])
    country = StringField(
        'Country', [
            validators.required(), validators.length(
                max=200)])
    degree = RadioField('Degree',
                        choices=[('option1', 'Option 1'), ('option2',
                                                           'Option 2'), ('other', 'It\'s complicated')],
                        coerce=get_coerce_val())
    comments = TextAreaField('Comments', [validators.optional()])

    def to_user_data(self):
        user_data = {
            'bitcoinAddress': self.pubkey.data,
            'email': self.email.data,
            'firstName': self.first_name.data,
            'lastName': self.last_name.data,
            'comments': self.comments.data,
            'degree': self.degree.data,
            'address': self.address.data,
            'city': self.city.data,
            'state': self.state.data,
            'zipCode': self.zipcode.data,
            'country': self.country.data
        }
        return user_data

    def to_user_data_legacy(self):
        user_json = {'pubkey': self.pubkey.data, 'info': {}}
        user_json['info']['email'] = self.email.data
        user_json['info']['degree'] = self.degree.data
        user_json['info']['comments'] = self.comments.data
        user_json['info']['name'] = {'familyName': self.last_name.data, 'givenName': self.first_name.data}
        user_json['info']['address'] = {
            'streetAddress': self.address.data,
            'city': self.city.data,
            'state': self.state.data,
            'zipcode': "\'" + self.zipcode.data,  # TODO: per discussion, ' was added to help export. Find another way
            'country': self.country.data
        }
        return user_json
