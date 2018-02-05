import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import os
from pkg_resources import Requirement, resource_filename
import json

class EmailAlerter:

    def __init__(self, settings):
        self.settings = settings
    
    @classmethod
    def from_filepath(cls, email_settings_filepath):
        try:
            email_settings = json.load(open(email_settings_filepath, 'r'))
            return cls(email_settings)
        except Exception as e:
            print(e)
            print('Failure loading email settings file. Falling back on default.')
            return EmailAlerter(settings={'email_alerts_enabled' : False})

    def send_message(self, experiment_name, log_file_directory, success):
        if self.settings['email_alerts_enabled']:
            sender = self.settings['sender_email_address']
            recipients = self.settings['recipient_email_address_list']
            attachments = [ os.path.join(log_file_directory, filename) for filename in self.settings['email_attachments'] ]
            date = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
            status = 'succeeded' if success else 'failed'

            msg = MIMEMultipart()
            msg['Subject'] = self.settings['email_subect_line'].format(timestamp = date, job_id = experiment_name, job_status=status)
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)
        
            if success:
                body = self.settings['success_message'].format(timestamp = date, job_id = experiment_name, job_status=status)
            else:
                body = self.settings['failure_message'].format(timestamp = date, job_id = experiment_name, job_status=status)
            msg.attach(MIMEText(body))

            for filename in attachments:
                try:
                    with open(filename, 'r') as f:
                        attachment = MIMEText(f.read())
                    msg.attach(attachment)
                    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                except:
                    print('Error attaching file \'{}\' to email'.format(filename))

            # Send the email via the specified SMTP server.
            try:
                with smtplib.SMTP(self.settings['sender_email_server_address'], self.settings['sender_email_server_port']) as server:
                    server.login(self.settings['sender_email_address'], self.settings['sender_email_password'])
                    server.sendmail(sender, recipients, msg.as_string())
            except Exception as e:
                print('Failed to send email.')
