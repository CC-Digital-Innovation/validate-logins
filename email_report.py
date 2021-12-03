import configparser
import smtplib
import ssl
from email.message import EmailMessage

# read and parse config file
config = configparser.ConfigParser()
config.read('config.ini')

smtp_server = config['email']['server']
port = config['email']['port']
user = config['email']['user']
password = config['email']['password']
sender_email = config['email']['from']
receiver = config['email']['to']
maintainer = config['email']['maintainer_email']

context = ssl.create_default_context()

def send_email(subject, message):
    # create message
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver
    msg.set_content(f'''Report is create and sent as an HTML, and is only visibile with clients that can render HTML emails.
                       Contact at {maintainer} if there are any issues.''')
    msg.add_alternative(message, subtype='html')
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls(context=context)
        server.login(user, password)
        server.send_message(msg)

def send_validate_report(result):
    company_name = config['snow']['company']
    subject = f'Login Validation Report for {company_name}'
    html_builder = []
    html_builder.append(f'''\
        <!DOCTYPE html>
        <html>
        <head>
        <title>Autoamted Login Validation</title>
        <style>
            table {{
                border: 1px solid black;
                border-collapse: collapse;
            }}
        ​
            th {{
                border: 1px solid black;
                padding: 3px;
                background-color: #08088A;
                color: white;
                font-size: 100%;
            }}
        ​
            td {{
                border: 1px solid black;
                padding: 3px;
                font-size: 100%;
            }}
        </style>
        </head>
        <body>
            <h1>Login Validation Repoort for {company_name}</h1>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Host</th>
                        <th>User</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
        ''')
    for ci in result:
        html_builder.append(f'''\
            <tr>
                <td><a href="{ci['link']}">{ci['name']}</a></td>
                <td>{ci['host']}</td>
                <td>{ci['user']}</td>
                <td>{ci['status']}</td>
            </tr>
            ''')
    html_builder.append('''\
                </tbody>
            </table>
        </body>
        </html>
        ''')
    message = ''.join(html_builder)
    send_email(subject, message)