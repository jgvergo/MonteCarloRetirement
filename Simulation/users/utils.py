import os
import secrets
from PIL import Image
from flask import url_for, current_app
from flask_mail import Message
from Simulation import mail
from dateutil.relativedelta import relativedelta


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message(subject='Password Reset Request',
                  sender='jgvergo@gmail.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

# Calculate age in years given two dates
def calculate_age(date1, date2):
    return date1.year - date2.year - ((date1.month, date1.day) < (date2.month, date2.day))


# Currently unused
def calculate_full_ss_date(birthday):
    if birthday.year <= 1937:
        year = 65
        month = 0
    elif birthday.year == 1938:
        year = 65
        month = 2
    elif birthday.year == 1939:
        year = 65
        month = 4
    elif birthday.year == 1940:
        year = 65
        month = 6
    elif birthday.year == 1941:
        year = 65
        month = 8
    elif birthday.year == 1942:
        year = 65
        month = 10
    elif (birthday.year >= 1943) and (birthday.year <= 1954):
        year = 66
        month = 0
    elif birthday.year == 1955:
        year = 66
        month = 2
    elif birthday.year == 1956:
        year = 66
        month = 4
    elif birthday.year == 1957:
        year = 66
        month = 6
    elif birthday.year == 1958:
        year = 66
        month = 8
    elif birthday.year == 1959:
        year = 66
        month = 10
    elif birthday.year >= 1960:
        year = 67
        month = 00
    full_ss_date = birthday + relativedelta(years=year, months=month)
    return full_ss_date




def get_key(dict, val):
    for key, value in dict.items():
        if val == value:
            return key
    return "NoKey"

def does_key_exist(dict, chk_key):
    for key, value in dict.items():
        if key == chk_key:
            return True
    return False