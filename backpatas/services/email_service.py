from flask import current_app
from flask_mail import Message
from backpatas.extensions import mail

def send_email(to: str, subject: str, body: str):
    """
    Envío simple (texto plano). Si quieres HTML, se agrega msg.html.
    """
    if not to:
        return

    msg = Message(
        subject=subject,
        recipients=[to],
        body=body,
        sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
    )
    mail.send(msg)
