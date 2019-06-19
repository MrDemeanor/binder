from app import db
from app.models import UserModel, SemesterModel, ClassModel, OverrideModel

new_user = UserModel(
    id = 'mw13', 
    firstname = 'Max', 
    lastname = 'Wittorp', 
    email = 'mw13@txstate.edu', 
    authentication_level = 3
)

new_user.set_password('P@radox1998')
db.session.add(new_user)
db.session.commit()