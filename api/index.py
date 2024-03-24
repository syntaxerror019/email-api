from flask import Flask, request, jsonify
import requests
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

app = Flask(__name__)

UPLOAD_FOLDER = 'tmp'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def send_mail(sender_email, sender_password, receiver_email, subject, body, files):
    try:
        # Create a multipart message and set headers
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = receiver_email
        message['Subject'] = subject

        message.attach(MIMEText(body, 'plain'))

        for file_path in files:
            attachment = open(file_path, 'rb')
            part = MIMEBase('application', 'octet-stream')
            part.set_payload((attachment).read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(file_path))
            message.attach(part)
            attachment.close()
            # Delete the file after attaching
            os.remove(file_path)

        # Create SMTP session for sending the mail
        with smtplib.SMTP('smtp.gmail.com', 587) as session:
            session.starttls()
            session.login(sender_email, sender_password)
            text = message.as_string()
            session.sendmail(sender_email, receiver_email, text)
        return True
    except Exception as e:
        return e

@app.route('/sendmail', methods=['POST'])
def send_mail_route():
    files = []
    
    #  data from request
    url_files = request.json.get('attachments', [])

    sender_email = request.json.get('sender_email')
    sender_password = request.json.get('sender_password')
    receiver_email = request.json.get('receiver_email')
    subject = request.json.get('subject')
    body = request.json.get('body')

    # hhandle files from URLs
    for url in url_files:
        response = requests.get(url)
        if response.status_code == 200:
            filename = os.path.basename(url)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            files.append(file_path)


    # Send email with attachments
    success = send_mail(sender_email, sender_password, receiver_email, subject, body, files)
    if not success:
        return jsonify({'error': 'Failed to send email', 'error': str(success)})
    return jsonify({'message': 'Email sent successfully'})

if __name__ == '__main__':
    app.run()
