from app import db
from app.models import UserModel, SemesterModel, ClassModel, OverrideModel

new_user = UserModel(
    id = 'btr26', 
    firstname = 'Brent', 
    lastname = 'Redmon', 
    email = 'btr26@txstate.edu', 
    authentication_level = 3
)

new_user.set_password('P@radox1998')
db.session.add(new_user)
db.session.commit()