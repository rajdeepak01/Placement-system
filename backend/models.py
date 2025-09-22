from  .database import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(), unique = True, nullable = False)
    email = db.Column(db.String(), unique = True, nullable = False)
    password = db.Column(db.String(), nullable = False)
    skills = db.Column(db.String, nullable=True)
    type = db.Column(db.String(), default = 'general')
    ebooks = db.relationship('Ebook', backref="bearer")


class Ebook(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(), nullable = False)
    author = db.Column(db.String(), nullable = False)
    url = db.Column(db.String(), nullable = False)
    status = db.Column(db.String(), default = 'available')
    job_desc = db.Column(db.String, nullable = True)
    job_title = db.Column(db.String, nullable = True)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)


# One to Many relationship: one user can book multiple books