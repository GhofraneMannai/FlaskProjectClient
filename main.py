from flask import Flask, render_template, request, redirect, url_for, session, flash,jsonify  
from flask_mysqldb import MySQL
import os
from MySQLdb.cursors import DictCursor  # Import DictCursor
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid  # Add this line to import the uuid module
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer as Serializer, BadSignature, SignatureExpired

# Configure Flask-Mail

app = Flask(__name__, template_folder='template', static_url_path='/static', static_folder='static')
# Initialize Flask-Mail
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Replace with your mail server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ghofranemn22@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'lexh jter nxjy ioxu'  # Replace with your email password
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@example.com'

mail = Mail(app)

# Set the secret key to enable sessions
app.secret_key = 'your_secret_key_here'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'stage'
app.config['UPLOAD_FOLDER'] = '/static/img/'

mysql = MySQL(app)

def generate_confirmation_token(email):
    s = Serializer(app.config['SECRET_KEY'])
    return s.dumps({'email': email}, salt='email-confirmation')

def confirm_token(token, expiration=3600):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token, salt='email-confirmation', max_age=expiration)
    except (BadSignature, SignatureExpired):
        return None
    return data['email']
@app.route('/', methods=['GET', 'POST'])
def index():

    
    return render_template('index.html')


@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    return render_template('contact.html')

@app.route('/faq', methods=['GET', 'POST'])
def faq():
    return render_template('faq.html')


@app.route('/feature', methods=['GET', 'POST'])
def feature():
    return render_template('feature.html')


@app.route('/project', methods=['GET', 'POST'])
def project():
    return render_template('project.html')


@app.route('/service', methods=['GET', 'POST'])
def service():
    return render_template('service.html')



@app.route('/team', methods=['GET', 'POST'])
def team():
    return render_template('team.html')

@app.route('/testimonial', methods=['GET', 'POST'])
def testimonial():
    return render_template('testimonial.html')



@app.route('/customer', methods=['GET', 'POST'])
def customer():
    return render_template('customer.html')


#Client
@app.route('/add', methods=['POST'])
def add():
    errors = []

    # Get form data
    name = request.form.get('name')
    surname = request.form.get('surname')
    email = request.form.get('email')
    company = request.form.get('company')
    address = request.form.get('address')
    phone = request.form.get('phone')
    dob = request.form.get('dob')
    deadline = request.form.get('deadline')
    poste = request.form.get('poste')
    title_project = request.form.get('title_project')
    description = request.form.get('description')
    
    decisionMail = "Not Confirmed"
    badgeMail = "warning"
    badgeValidate = "warning"
    decisionvalidate = "Not Validated"

    # Validation checks
    required_fields = {
        'Name': name,
        'Surname': surname,
        'Company': company,
        'Date of Birth': dob,
        'Deadline': deadline,
        'Post': poste,
        'Address': address,
        'Email': email,
        'Title of the project': title_project,
        'Description': description,
        'Phone': phone
    }
    
    for field, value in required_fields.items():
        if not value:
            errors.append(f'{field} is required.')

    if len(phone) < 9:
        errors.append('Phone number must be at least 9 digits.')

    # Parse and validate dates
    try:
        dob_date = datetime.strptime(dob, '%Y-%m-%d')
        deadline_date = datetime.strptime(deadline, '%Y-%m-%d')
        current_date = datetime.now()

        if dob_date >= current_date:
            errors.append('Date of birth must be in the past.')
        if deadline_date <= current_date:
            errors.append('Deadline must be in the future.')

    except ValueError:
        errors.append('Invalid date format. Use YYYY-MM-DD.')

    # Return errors if any
    if errors:
        return jsonify({'status': 'error', 'errors': errors})

    # Handle image upload
    image = request.files.get('image')
    if image:
        # Generate unique image name to prevent collisions
        image_extension = image.filename.rsplit('.', 1)[1].lower()
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if image_extension not in allowed_extensions:
            errors.append('Invalid image type. Allowed types: png, jpg, jpeg, gif.')
        else:
            image_name = f"{uuid.uuid4().hex}.{image_extension}"
            image_path = os.path.join('static', 'faces', image_name)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            image.save(image_path)
    else:
        image_name = None  # Set image_name to None if no image is provided

    # Insert data into MySQL database
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO clients (
                nom, prenom, nomEntreprise, email, adress, phone, dateBirth, deadline, poste, titleprojet, description, image, decisionMail, badgeMail, decisionValidate, badgeValidate
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, 
            (name, surname, company, email, address, phone, dob, deadline, poste, title_project, description, image_name, decisionMail, badgeMail, decisionvalidate, badgeValidate))
        mysql.connection.commit()
        cur.close()

        # Generate confirmation email
        token = generate_confirmation_token(email)
        confirmation_url = url_for('confirm_email', token=token, _external=True)

        msg = Message('Client Added Successfully', sender=app.config['MAIL_DEFAULT_SENDER'], recipients=[email])
        msg.html = render_template('confirmation_email.html', name=name, confirmation_url=confirmation_url)
        mail.send(msg)

        return jsonify({'status': 'success', 'redirect_url': url_for('index')})

    except Exception as e:
        return jsonify({'status': 'error', 'errors': [str(e)]})

    return redirect(url_for('index'))


@app.route('/confirm/<token>')
def confirm_email(token):
    email = confirm_token(token)
    if email:
        try:
            # Update the database to confirm the email
            cur = mysql.connection.cursor()
            cur.execute("""UPDATE clients SET decisionMail = %s, badgeMail = %s WHERE email = %s""", ('Confirmed', 'success', email))
            mysql.connection.commit()
            cur.close()

            # Render a confirmation page
            return render_template('confirmation_success.html', name=email)
        except Exception as e:
            return render_template('confirmation_error.html', message=str(e))
    else:
        return render_template('confirmation_error.html', message="The confirmation link is invalid or has expired.")


#Candidate
@app.route('/addCandidat', methods=['POST'])
def addCandidat():
    if request.method == 'POST':
        errors = []

        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        phone = request.form['phone']
        commentaire = request.form['commentaire']

        if not name:
            errors.append('Name is required.')
        if not surname:
            errors.append('Surname is required.')
        if not email:
            errors.append('Email is required.')
        if not commentaire:
            errors.append('Commentaire is required.')
        if not phone:
            errors.append('Phone number is required.')
        elif len(phone) < 9:
            errors.append('Phone number must be at least 9 digits.')

        if errors:
            return jsonify({'status': 'error', 'errors': errors})

        image = request.files['image']
        # Define the path where the image will be saved
        image_name = image.filename
        image_path = os.path.join('static', 'faces', image_name)

        # Ensure the directory exists
        os.makedirs(os.path.dirname(image_path), exist_ok=True)

        # Save the image
        image.save(image_path)
        print(errors);


        cv = request.files['cv']
        
        cv_name = cv.filename
        cv_path = os.path.join('static', 'CV', cv_name)

      
        os.makedirs(os.path.dirname(cv_path), exist_ok=True)

       
        cv.save(cv_path)
      

        # Insert into MySQL database
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO candidats (
                nom, prenom,image,email, telephone, CV, Commentaire
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (name, surname, image_name, email , phone,  cv_name ,commentaire))
        mysql.connection.commit()
        cur.close()

        return jsonify({'status': 'success'})

    return redirect(url_for('index'))




@app.route('/add_message', methods=['POST'])
def add_message():
    # Get form data
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')

    # Basic validation
    errors = []
    if not name:
        errors.append('Name is required.')
    if not email:
        errors.append('Email is required.')
    if not subject:
        errors.append('Subject is required.')
    if not message:
        errors.append('Message is required.')

    # Return errors if any
    if errors:
        return jsonify({'status': 'error', 'errors': errors})

    # Insert data into MySQL database
    try:
        cur = mysql.connection.cursor(DictCursor)
        cur.execute("""
            INSERT INTO contact (nom, email, objet, message)
            VALUES (%s, %s, %s, %s)
        """, (name, email, subject, message))
        mysql.connection.commit()

        # Retrieve the createdAt timestamp of the newly inserted row
        last_id = cur.lastrowid
        cur.execute("SELECT createdAt FROM contact WHERE id = %s", (last_id,))
        created_at = cur.fetchone()['createdAt']

        cur.close()
        return jsonify({'status': 'success', 'message': 'Message added successfully!', 'createdAt': created_at})

    except Exception as e:
        return jsonify({'status': 'error', 'errors': [str(e)]})
   


if __name__ == '__main__':
    app.run(debug=True)