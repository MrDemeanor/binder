from app import db
from app.models import UserModel, SemesterModel, ClassModel, OverrideModel

new_user = UserModel(
    id = '', 
    firstname = '', 
    lastname = '', 
    email = '', 
    department = "",
    authentication_level = 3
)

new_user.set_password('')
db.session.add(new_user)
db.session.commit()