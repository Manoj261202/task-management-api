import os
from fastapi import BackgroundTasks

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "your_email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your_app_password")

def fake_send_email(to_email: str, subject: str, body: str):
    print("----- Sending email -----")
    print("To:", to_email)
    print("Subject:", subject)
    print("Body:", body)
    print("-------------------------")

def send_email_background(background_tasks: BackgroundTasks, email_to: str, subject: str, body: str):
    background_tasks.add_task(fake_send_email, email_to, subject, body)

def send_email_smtp(email_to: str, subject: str, body: str):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_USER
    msg["To"] = email_to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, email_to, msg.as_string())
