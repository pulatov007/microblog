from threading import Thread
from flask import render_template
from flask_mail import Message
from app import app, mail


def _send_async(flask_app, msg):
    with flask_app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=_send_async, args=(app, msg)).start()


def send_password_reset_email(usr):
    token = usr.get_reset_password_token()
    send_email('[Pulatov Blog] Réinitialisation de votre mot de passe',
               sender=app.config['ADMINS'][0],
               recipients=[usr.email],
               text_body=render_template('email/reset_password.txt',
                                         user=usr, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=usr, token=token))
