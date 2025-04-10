import boto3
from botocore.exceptions import ClientError
from flask import Flask
from flaskext.mysql import MySQL
import json
from flask import request, render_template

app = Flask(__name__)

# Function to retrieve secrets from AWS Secrets Manager
def get_secret():
    secret_name = "paul-aws-flask-demo-credential11"
    region_name = "us-east-1"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    # Parse the secret string as JSON
    secret = json.loads(get_secret_value_response['SecretString'])
    
    return secret

# Retrieve the secrets
secrets = get_secret()

app = Flask(__name__)

# Configure mysql database
app.config['MYSQL_DATABASE_HOST'] = secrets['host']
app.config['MYSQL_DATABASE_USER'] = secrets['username']
app.config['MYSQL_DATABASE_PASSWORD'] = secrets['password']
app.config['MYSQL_DATABASE_DB'] = secrets['dbname']
app.config['MYSQL_DATABASE_PORT'] = secrets['port']
mysql = MySQL()
mysql.init_app(app)
connection = mysql.connect()
connection.autocommit(True)
cursor = connection.cursor()

# Create users table within MySQL db and populate with sample data
# Execute the code below only once.
# Write sql code for initializing users table..
drop_table = 'DROP TABLE IF EXISTS users;'
users_table = """
CREATE TABLE users (
  username varchar(50) NOT NULL,
  email varchar(50),
  PRIMARY KEY (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""
data = """
INSERT INTO ondia.users 
VALUES 
    ("dora", "dora@amazon.com"),
    ("john", "john@google.com"),
    ("sencer", "sencer@bmw.com"),
    ("uras", "uras@mercedes.com"),
	("ares", "ares@porche.com");
"""
cursor.execute(drop_table)
cursor.execute(users_table)
cursor.execute(data)

# Write a function named `find_emails` which find emails using keyword from the user table in the db,
# and returns result as tuples `(name, email)`.

def find_emails(keyword):
    query = f"""
    SELECT * FROM users WHERE username like '%{keyword}%';
    """
    cursor.execute(query)
    result = cursor.fetchall()
    user_emails = [(row[0], row[1]) for row in result]
    # if there is no user with given name in the db, then give warning
    if not any(user_emails):
        user_emails = [('Not found.', 'Not Found.')]
    return user_emails

# Write a function named `insert_email` which adds new email to users table the db.
def insert_email(name, email):
    query = f"""
    SELECT * FROM users WHERE username like '{name}';
    """
    cursor.execute(query)
    result = cursor.fetchall()
    # default text
    response = ''
    # if user input are None (null) give warning
    if len(name) == 0 or len(email) == 0:
        response = 'Username or email can not be empty!!'
    # if there is no same user name in the db, then insert the new one
    elif not any(result):
        insert = f"""
        INSERT INTO users
        VALUES ('{name}', '{email}');
        """
        cursor.execute(insert)
        response = f'User {name} and {email} have been added successfully'
    # if there is user with same name, then give warning
    else:
        response = f'User {name} already exits.'
    return response

# Write a function named `emails` which finds email addresses by keyword using `GET` and `POST` methods,
# using template files named `emails.html` given under `templates` folder
# and assign to the static route of ('/')
@app.route('/', methods=['GET', 'POST'])
def emails():
    if request.method == 'POST':
        user_name = request.form['user_keyword']
        user_emails = find_emails(user_name)
        return render_template('emails.html', name_emails=user_emails, keyword=user_name, show_result=True)
    else:
        return render_template('emails.html', show_result=False)

# Write a function named `add_email` which inserts new email to the database using `GET` and `POST` methods,
# using template files named `add-email.html` given under `templates` folder
# and assign to the static route of ('add')
@app.route('/add', methods=['GET', 'POST'])
def add_email():
    if request.method == 'POST':
        user_name = request.form['username']
        user_email = request.form['useremail']
        result = insert_email(user_name, user_email)
        return render_template('add-email.html', result_html=result, show_result=True)
    else:
        return render_template('add-email.html', show_result=False)

# Add a statement to run the Flask application which can be reached from any host on port 80.
if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host='0.0.0.0', port=8080)