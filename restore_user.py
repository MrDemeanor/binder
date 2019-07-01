from app import db
from app.models import UserModel, SemesterModel, ClassModel, OverrideModel

new_user = UserModel(
    # class_jurisdiction = "MGT,B+A",
    # department = "MGT",
    email = "admin26@txstate.edu",
    firstname = "Admin",
    id = "Admin",
    lastname = "Admin", 
    authentication_level = 3
)

new_user.set_password('1234')
db.session.add(new_user)
db.session.commit()