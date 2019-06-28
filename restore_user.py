from app import db
from app.models import UserModel, SemesterModel, ClassModel, OverrideModel

new_user = UserModel(
    class_jurisdiction = "MGT,B+A",
    department = "MGT",
    email = "btr26@txstate.edu",
    firstname = "Brent",
    id = "btr26",
    lastname = "btr26", 
    authentication_level = 2
)

new_user.set_password('1234')
db.session.add(new_user)
db.session.commit()