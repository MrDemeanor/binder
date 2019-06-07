from marshmallow_sqlalchemy import ModelSchema
from app.models import UserModel, SemesterModel, ClassModel, OverrideModel

class UserSchema(ModelSchema):
    class Meta:
        model = UserModel

class SemesterSchema(ModelSchema):
    class Meta:
        model = SemesterModel

class ClassSchema(ModelSchema):
    class Meta:
        model = ClassModel

class OverrideSchema(ModelSchema):
    class Meta:
        model = OverrideModel

user_schema_many = UserSchema(many=True)
user_schema = UserSchema()

semester_schema_many = SemesterSchema(many=True)
semester_schema = SemesterSchema()

class_schema_many = ClassSchema(many=True)
class_schema = ClassSchema()

override_schema_many = OverrideSchema(many=True)
override_schema = OverrideSchema()