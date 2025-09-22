from flask import Flask
from backend.database import *

app = None 

def create_app():
    app = Flask(__name__)
    app.debug = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///TPC.sqlite3"
    db.init_app(app)
    app.app_context().push()
    return app

app = create_app()

from backend.controllers import *

if __name__=="__main__":
    # db.create_all()
    # user1 = User(username = 'admin123', email = "admin@user.com", password = '1234', type = 'admin')
    # db.session.add(user1)
    # db.session.commit()
    # print("Database created!")
    app.run()