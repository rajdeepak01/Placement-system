from flask import Flask, render_template, redirect, request, url_for
from flask import current_app as app
from .models import *
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

@app.route('/')
def home():
    return render_template('/landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form['username']
        pwd = request.form['pwd']
        this_user = User.query.filter_by(username=username).first()
        if this_user:
            if this_user.password == pwd:
                if this_user.type == "admin":
                    return redirect('/admin')
                elif this_user.type=="company":
                    return redirect(f'/company_dash/{this_user.id}')
                else:
                    return redirect(f'/user_dash/{this_user.id}')
            else:
                return render_template('login.html', msg="Invalid password try again")
        else:
            return render_template('login.html', msg="User does not exist")
    return render_template('login.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['pwd']
        email = request.form['email']
        skills = request.form['skills']
        user_name = User.query.filter_by(username=username).first()
        user_email = User.query.filter_by(email=email).first()
        if user_name or user_email:
            return render_template("login.html", msg="User Already exist please login")
        else:
            user = User(username = username,
                        password=password,
                        email = email,
                        skills=skills)
            db.session.add(user)
            db.session.commit()
        return render_template("login.html", msg="registed successfully please login buddy!")
    return render_template('register.html')

def compute_match_ratio(user_skills, ebook_text):
    """
    Calculate the ratio of skills matching in ebook text.
    """
    if not user_skills:
        return 0
    
    skills_list = [s.strip().lower() for s in user_skills.split(',')]
    ebook_text = ebook_text.lower()
    
    matches = sum(1 for skill in skills_list if skill in ebook_text)
    ratio = matches / len(skills_list)
    
    return round(ratio, 2)


@app.route('/admin')
def admin():
    # Get admin user
    this_user = User.query.filter_by(type="admin").first()
    
    # Other users (exclude admin)
    users = User.query.filter(User.type != "admin").all()
    
    # Ebooks
    pen_ebooks = Ebook.query.filter_by(status="granted").all()
    req_ebooks = Ebook.query.filter_by(status="requested").all()
    
    # Stats
    aval = Ebook.query.filter_by(status="available").count()
    grant = Ebook.query.filter_by(status="granted").count()
    reqs = len(req_ebooks)
    
    # Add match_ratio to requested ebooks
    for ebook in req_ebooks:
        user = ebook.bearer
        if user and user.skills:
            ebook.match_ratio = compute_match_ratio(user.skills, f"{ebook.name} {ebook.author} {ebook.url}")
        else:
            ebook.match_ratio = 0

    # Add match_ratio to pending ebooks (optional)
    for ebook in pen_ebooks:
        user = ebook.bearer
        if user and user.skills:
            ebook.match_ratio = compute_match_ratio(user.skills, f"{ebook.name} {ebook.author} {ebook.url}")
        else:
            ebook.match_ratio = 0

    return render_template(
        'admin_dash.html', 
        this_user=this_user,
        req_ebooks=req_ebooks,
        pen_ebooks=pen_ebooks,
        users=len(users),
        reqs=reqs,
        aval=aval,
        grant=grant,
        pen_ebooks_count=len(pen_ebooks)
    )

@app.route("/add_company", methods=["GET", "POST"])
def add_company():
    this_user = User.query.filter_by(type="admin").first()  # admin for navbar

    if request.method == "POST":
        name = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("pwd")
        existing = User.query.filter((User.username==name) | (User.email==email)).first()
        if existing:
            return redirect("/add_company")

        company = User(
            username=name,
            email=email,
            password=password,
            type="company"
        )
        db.session.add(company)
        db.session.commit()
        return redirect("/admin")

    return render_template("add_company.html", this_user=this_user)

@app.route("/partners")
def partners():
    this_user = User.query.filter_by(type="admin").first()  # for navbar
    companies = User.query.filter_by(type="company").all()  # fetch all companies
    return render_template("partners.html", this_user=this_user, companies=companies)


@app.route("/user_dash/<int:user_id>")
def user_dash(user_id):
    this_user = User.query.filter_by(id = user_id).first()
    grant = Ebook.query.filter_by(status = "granted", user_id=this_user.id).all()
    req = Ebook.query.filter_by(status = "requested", user_id=this_user.id).all()
    ebook = Ebook.query.all()
    return render_template("user_dash.html", this_user=this_user, grant=grant, req=req, ebook=ebook)


@app.route('/create-ebook', methods=["GET", "POST"])
def create():
    this_user= User.query.filter_by(type="admin").first()
    if request.method == "POST":
        name = request.form.get("name")
        author = request.form.get("author")
        url = request.form.get("url")
        ebook = Ebook(name = name, author=author, url=url)
        db.session.add(ebook)
        db.session.commit()
        return redirect('/admin')
    return render_template("create_eb.html")

@app.route("/request-ebook/<int:user_id>")
def request_ebook(user_id):
    this_user = User.query.filter_by(id = user_id).first()
    ebooks = Ebook.query.filter_by(status = "available").all()
    return render_template("request.html", this_user=this_user, ebooks=ebooks)

@app.route('/request/<int:ebook_id>/<int:user_id>')
def req_eb(ebook_id, user_id):
    this_user = User.query.get(user_id)
    ebook = Ebook.query.get(ebook_id)
    ebook.status = "requested"
    ebook.user_id = user_id
    db.session.commit()
    return redirect(f"/user_dash/{this_user.id}")

@app.route('/return/<int:ebook_id>/<int:user_id>')
def return_ebook(ebook_id, user_id):
    this_user = User.query.get(user_id)
    ebook = Ebook.query.get(ebook_id)
    ebook.status = "pending"
    ebook.user_id = user_id
    db.session.commit()
    return redirect(f"/user_dash/{this_user.id}")

@app.route('/approve_return/<int:ebook_id>/<int:user_id>')
def approve_return_ebook(ebook_id, user_id):
    this_user = User.query.get(user_id)
    ebook = Ebook.query.get(ebook_id)
    ebook.status = "available"
    ebook.user_id = None
    db.session.commit()
    return redirect("/admin")


@app.route("/grant/<int:ebook_id>/<int:user_id>")
def grant_eb(ebook_id, user_id):
    this_user = User.query.get(user_id)
    ebook = Ebook.query.filter_by(id=ebook_id, user_id = user_id).first()
    ebook.status = "granted"
    ebook.user_id = user_id
    db.session.commit()
    return redirect('/admin')


@app.route("/return_approve/<int:ebook_id>/<int:user_id>")
def return_approve(ebook_id, user_id):
    this_user = User.query.get(user_id)
    ebook = Ebook.query.filter_by(id=ebook_id, user_id = user_id).first()
    ebook.status = "available"
    ebook.user_id = user_id
    db.session.commit()
    return redirect('/admin')

@app.route("/search")
def search():
    search_word = request.args.get("search")
    key = request.args.get("key")
    if key == "user":
        results = User.query.filter_by(username = search_word).all()
    else:
        results = Ebook.query.filter_by(name = search_word).all()
    return render_template("results.html", results=results, key = key)

@app.route('/view/<ebook>/<int:user_id>')
def view(ebook, user_id):
    this_user = User.query.filter_by(id = user_id).first()
    details =  Ebook.query.filter_by(user_id=user_id, name=ebook).all()
    return render_template('view.html', details=details, this_user=this_user)

@app.route("/summary")
def summary():
    this_user = User.query.filter_by(type='admin').first()
    av = len(Ebook.query.filter_by(status = "available").all())
    re = len(Ebook.query.filter_by(status = "requested").all())
    gr = len(Ebook.query.filter_by(status = "granted").all())
    pen = len(Ebook.query.filter_by(status = "pending").all())

# pie chart (generated cards)
    labels = ['available', 'requested', 'granted', "pending"]
    sizes = [av, re, gr, pen]
    colors = ['blue', 'yellow', 'green', 'pink']
    plt.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%")
    plt.title("status of Jobs")
    plt.savefig("static/pie.png")
    plt.clf()

#bar graph (requested cards)
    labels = ['available', 'requested', 'granted', "pending"]
    sizes = [av, re, gr, pen]
    plt.bar(labels, sizes)
    plt.xlabel("status of E-books")
    plt.ylabel("No of E-books")
    plt.title("Jobs Status Distribution")
    plt.savefig("static/bar.png")
    plt.clf()

    return render_template("/summary.html", av=av, re = re, gr=gr, pen=pen, this_user=this_user)

@app.route("/user_summary/<int:user_id>")
def user_summary(user_id):
    this_user = User.query.filter_by(id = user_id).first()
    re = len(Ebook.query.filter_by(status = "requested").all())
    gr = len(Ebook.query.filter_by(status = "granted").all())

# pie chart (generated cards)
    labels = ['requested', 'granted']
    sizes = [re, gr]
    colors = ['yellow', 'green']
    plt.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%")
    plt.title("status of Placement")
    plt.savefig("static/pie.png")
    plt.clf()

#bar graph (requested cards)
    labels = ['requested', 'granted']
    sizes = [re, gr]
    plt.bar(labels, sizes)
    plt.xlabel("status of Placement")
    plt.ylabel("No of E-books")
    plt.title("Placement Status Distribution")
    plt.savefig("static/bar.png")
    plt.clf()
    return render_template("/user_summary.html",re = re, gr=gr, this_user=this_user)

from flask import render_template, request, redirect
from werkzeug.security import generate_password_hash
from .models import User
from .database import db

@app.route("/user_profile/<int:user_id>", methods=["GET", "POST"])
def user_profile(user_id):
    this_user = User.query.get_or_404(user_id)
    
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        skills = request.form.get("skills")
        password = request.form.get("password") 

        # Update fields if provided
        if username:
            this_user.username = username
        if email:
            this_user.email = email
        this_user.skills = skills or ""

        if password:
            this_user.password = generate_password_hash(password)

        # Commit changes
        db.session.commit()
        
        return redirect(f"/user_dash/{this_user.id}")

    # GET request
    return render_template("user_profile.html", user=this_user)

@app.route("/company_dash/<int:user_id>")
def company_dash(user_id):
    # Get the company
    this_company = User.query.filter_by(type="company", id=user_id).first()
    
    if not this_company:
        return "Company not found", 404

    # Fetch only granted ebooks where author matches company name
    granted_jobs = Ebook.query.filter_by(status="granted", author=this_company.username).all()

    # Fetch applications for these granted jobs
    applications = []
    for job in granted_jobs:
        if job.bearer:  # bearer is the user who got it
            applications.append({
                "id": job.bearer.id,
                "username": job.bearer.username,
                "skills": job.bearer.skills,
                "job_title": job.name
            })

    return render_template(
        "company_dash.html", 
        this_company=this_company, 
        jobs=granted_jobs, 
        applications=applications
    )
