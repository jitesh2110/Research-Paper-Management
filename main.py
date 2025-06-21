import os
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory,session
from flask_bootstrap import Bootstrap

from datetime import date, datetime

from sqlalchemy import ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_migrate import Migrate
from xhtml2pdf import pisa
from io import BytesIO
from flask import make_response
import smtplib
import random
import bleach

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ResearchHub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = r"C:\PythonProject\Reserach Paper Ptojrct 0.1\Research-Paper\Static\Research_Document"
path = app.config['UPLOAD_FOLDER']
db = SQLAlchemy(app)

# Initialize after db
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"




class ResarchPaper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.Text, nullable=False)
    Abstract = db.Column(db.Text, nullable=False)
    Authors = db.Column(db.Text, nullable=False)
    Filepath = db.Column(db.String(250), nullable=False)
    DateUploaded = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    Citations = db.Column(db.Integer, nullable=True)

    Type = db.Column(db.String(50), nullable=False)  # e.g., Patent, Journal, Conference
    Journal_Conference_Name = db.Column(db.String(250), nullable=True)  # Name of journal or conference
    Publication_Date = db.Column(db.Date, nullable=True)  # Date of publication
    Paper_URL = db.Column(db.String(500), nullable=True)  # e.g., ijisaeurl or DOI link
    Conference_Venue = db.Column(db.String(250), nullable=True)

    ISSN = db.Column(db.String(100), nullable=True)
    ISBN = db.Column(db.String(100), nullable=True)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    Author = db.relationship("User", back_populates="Research")


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(500), nullable=False)

    citations = db.Column(db.Integer,nullable=True)
    college = db.Column(db.String(250), nullable=True)
    location = db.Column(db.String(250), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    about = db.Column(db.Text, nullable=True)
    fields = db.Column(db.String(250), nullable=True)
    collaboration = db.Column(db.String(50), nullable=True)
    profile_photo = db.Column(db.String(250), nullable=True)

    Research = db.relationship("ResarchPaper", back_populates="Author")


with app.app_context():
    db.create_all()




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/", methods=['GET', 'POST'])
def home():
    all_papers = ResarchPaper.query.order_by(ResarchPaper.DateUploaded.desc()).all()
    return render_template("home.html", all_papers=all_papers)


@app.route("/register/<int:x>", methods=['GET', 'POST'])
def register(x):
    if request.method == 'POST':

        if x==0:
            email = request.form['email']
            username = request.form['name']
            password = request.form['password']
            hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            new_user = User(user_name=username, email=email, password=hash)
            otp = random.randint(000000, 999999)

            session['email'] = email
            session['name'] = username
            session['password'] = password
            session['otp'] = otp

            with smtplib.SMTP('smtp.gmail.com') as connection:
                connection.starttls()
                connection.login(user='jsnewth@gmail.com', password='qrrc tibt icph shjo')
                connection.sendmail(from_addr='jsnewth@gmail.com', to_addrs=email,
                                    msg=f"Subject:Your OTP for ResearchHub!\n\n "
                                        f"OTP: {otp} buy now!")

            return render_template("otp.html")
        if x==1:
            user_otp = request.form['otp']
            real_otp = session.get('otp')

            if int(user_otp) == int(real_otp):
                email = session.get('email')
                username = session.get('name')
                password = session.get('password')
                hash_pw = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

                new_user = User(user_name=username, email=email, password=hash_pw)
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)


                session.pop('otp', None)
                session.pop('email', None)
                session.pop('name', None)
                session.pop('password', None)

                count = ResarchPaper.query.filter_by(author_id=new_user.id).count()
                return render_template("profile.html", user=new_user, count=count)
            else:
                return render_template("otp.html", error="Invalid OTP. Please try again.")

    return render_template("register.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            count = ResarchPaper.query.filter_by(author_id=user.id).count()
            return render_template("profile.html", user=user, count=count)

    return render_template("login.html")


@app.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/about", methods=['GET', 'POST'])
def about():
    return render_template("about.html")


@app.route("/profile/<int:id>", methods=['GET', 'POST'])
def profile(id):
    p = User.query.filter_by(id=id).first()
    count = ResarchPaper.query.filter_by(author_id=p.id).count()
    return render_template("profile.html", user=p, count=count)


@app.route("/add", methods=['GET', 'POST'])
@login_required
def takepaper():
    if request.method == 'POST':
        title = request.form['title']
        abstract = request.form['summary']
        authors = request.form['authors']
        paper_type = request.form['type']
        journal_name = request.form['journal_name']
        publication_date = request.form['publication_date']
        paper_url = request.form['paper_url']
        issn = request.form['issn']
        isbn = request.form['isbn']
        document = request.files['document']
        venew = request.form['conference_venue']


        file_name = document.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        document.save(file_path)

        # Convert date string to Python datetime object if provided
        pub_date = None
        if publication_date:
            pub_date = datetime.strptime(publication_date, "%Y-%m-%d")


        data = ResarchPaper(
            Title=title,
            Abstract=abstract,
            Authors=authors,
            Filepath=file_path,
            author_id=current_user.id,
            Conference_Venue=venew,
            Type=paper_type,
            Journal_Conference_Name=journal_name,
            Publication_Date=pub_date,
            Paper_URL=paper_url,
            ISSN=issn,
            ISBN=isbn
        )

        db.session.add(data)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template("takepaper.html")



@app.route("/showpaper/<int:id>", methods=['GET', 'POST'])
def showpaper(id):
    paper = ResarchPaper.query.get_or_404(id)
    return render_template("showpaper.html", paper=paper)

@app.route("/preview/<int:id>")
def preview_paper(id):
    paper = ResarchPaper.query.get_or_404(id)
    directory = os.path.dirname(paper.Filepath)
    filename = os.path.basename(paper.Filepath)
    return send_from_directory(directory, filename)

@app.route("/postcomment", methods=['GET', 'POST'])
def postcomment():
    return render_template("showpaper.html")


@app.route("/download/<path:filepath>/<int:id>")
def download(filepath,id):
    try:
        directory = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        paper = ResarchPaper.query.filter_by(id=id).first()
        paper.Citations = (paper.Citations or 0) + 1
        paper.Author.citations = (paper.Author.citations or 0) + 1

        db.session.commit()
        return send_from_directory(directory, filename, as_attachment=True)
    except Exception as e:
        return f"Error: {e}", 404


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.college = request.form['college']
        current_user.location = request.form['location']
        current_user.department = request.form['department']
        current_user.about = request.form['about']
        current_user.fields = request.form['fields']
        current_user.collaboration = request.form['collaboration']
        db.session.commit()

        photo = request.files.get('profile_photo')
        if photo and photo.filename != '':
            filename = photo.filename
            photo_path = os.path.join('static/profile_photos', filename)
            photo.save(photo_path)
            current_user.profile_photo = filename

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile', id=current_user.id))

    return render_template('edit_profile.html')


@app.route("/show_research_papers/<int:id>", methods=['GET', 'POST'])
def show_research_papers(id):
    all_papers = ResarchPaper.query.filter_by(author_id=id).all()
    return render_template("home.html", all_papers=all_papers)


@app.route("/search_ui/<int:a>",methods=['GET', 'POST'])
def search_ui(a):
    query = ResarchPaper.query

    # Get filter parameters from request
    title = request.args.get('title')
    author = request.args.get('author')
    paper_type = request.args.get('type')
    journal = request.args.get('journal')
    issn = request.args.get('issn')
    isbn = request.args.get('isbn')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    sort_by = request.args.get('sort_by')

    # Apply filters
    if title:
        query = query.filter(ResarchPaper.Title.ilike(f'%{title}%'))
    if author:
        query = query.filter(ResarchPaper.Authors.ilike(f'%{author}%'))
    if paper_type:
        query = query.filter(ResarchPaper.Type == paper_type)
    if journal:
        query = query.filter(ResarchPaper.Journal_Conference_Name.ilike(f'%{journal}%'))
    if issn:
        query = query.filter(ResarchPaper.ISSN == issn)
    if isbn:
        query = query.filter(ResarchPaper.ISBN == isbn)
    if start_date:
        query = query.filter(ResarchPaper.Publication_Date >= start_date)
    if end_date:
        query = query.filter(ResarchPaper.Publication_Date <= end_date)

    # Apply sorting
    if sort_by == 'date':
        query = query.order_by(ResarchPaper.Publication_Date.desc())
    elif sort_by == 'citations':
        query = query.order_by(ResarchPaper.Citations.desc())
    elif sort_by == 'title':
        query = query.order_by(ResarchPaper.Title.asc())

    results = query.all()

    if request.method == "POST" or a == 1:
        return  render_template('summary_template.html', papers=results, year=2025)
        #return render_template("home.html", all_papers=results)


    if request.method =="POST" or a==2:
        html = render_template('summary_template.html', papers=results, year=2025)
        # Create an in-memory buffer to hold the PDF
        pdf_output = BytesIO()

        # Generate the PDF and write it to the buffer
        pisa_status = pisa.CreatePDF(html, dest=pdf_output)

        # Check for any errors
        if pisa_status.err:
            return "PDF generation error!", 500

        # Get the value of the PDF from the buffer
        pdf_output.seek(0)  # Move to the start of the buffer

        # Prepare the response
        response = make_response(pdf_output.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=summary.pdf'

        return response


        return render_template("home.html", all_papers=results)

    return render_template("search.html")

if __name__ == "__main__":
    app.run(port=5001,debug=True)
