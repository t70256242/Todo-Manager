from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TimeField, SelectField, EmailField, PasswordField, TelField, \
    TextAreaField, DateField
from wtforms.validators import DataRequired, ValidationError

from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, TelField, TextAreaField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired

class SignUpForm(FlaskForm):
    first_name = StringField("",
                             validators=[DataRequired()],
                             render_kw={
                                 "placeholder": "First Name",
                                 "style": "width: 100%; padding: 12px; margin-bottom: 15px; "
                                          "border-radius: 5px; border: 1px solid #9B3922; "
                                          "background-color: #1A1A1A; color: #F2613F;"
                             })
    last_name = StringField("",
                            validators=[DataRequired()],
                            render_kw={
                                "placeholder": "Last Name",
                                "style": "width: 100%; padding: 12px; margin-bottom: 15px; "
                                         "border-radius: 5px; border: 1px solid #9B3922; "
                                         "background-color: #1A1A1A; color: #F2613F;"
                            })
    nickname = StringField("",
                           render_kw={
                               "placeholder": "Nickname",
                               "style": "width: 100%; padding: 12px; margin-bottom: 15px; "
                                        "border-radius: 5px; border: 1px solid #9B3922; "
                                        "background-color: #1A1A1A; color: #F2613F;"
                           })
    email = EmailField("",
                       validators=[DataRequired()],
                       render_kw={
                           "placeholder": "Email",
                           "style": "width: 100%; padding: 12px; margin-bottom: 15px; "
                                    "border-radius: 5px; border: 1px solid #9B3922; "
                                    "background-color: #1A1A1A; color: #F2613F;"
                       })
    password = PasswordField("",
                             validators=[DataRequired()],
                             render_kw={
                                 "placeholder": "Password",
                                 "style": "width: 100%; padding: 12px; margin-bottom: 15px; "
                                          "border-radius: 5px; border: 1px solid #9B3922; "
                                          "background-color: #1A1A1A; color: #F2613F;"
                             })
    phone = TelField("",
                     render_kw={
                         "placeholder": "Phone Number",
                         "style": "width: 100%; padding: 12px; margin-bottom: 15px; "
                                  "border-radius: 5px; border: 1px solid #9B3922; "
                                  "background-color: #1A1A1A; color: #F2613F;"
                     })
    address = StringField("",
                          render_kw={
                              "placeholder": "Address",
                              "style": "width: 100%; padding: 12px; margin-bottom: 15px; "
                                       "border-radius: 5px; border: 1px solid #9B3922; "
                                       "background-color: #1A1A1A; color: #F2613F;"
                          })
    bio = TextAreaField("",
                        render_kw={
                            "placeholder": "Bio",
                            "style": "width: 100%; padding: 12px; margin-bottom: 15px; "
                                     "border-radius: 5px; border: 1px solid #9B3922; "
                                     "background-color: #1A1A1A; color: #F2613F; height: 100px;"
                        })
    birthdate = DateField("",
                          validators=[DataRequired()],
                          render_kw={
                              "placeholder": "D.O.B",
                              "id": "birthdate",  # Add ID for Flatpickr targeting
                              "style": "width: 100%; padding: 12px; margin-bottom: 15px; "
                                       "border-radius: 5px; border: 1px solid #9B3922; "
                                       "background-color: #1A1A1A; color: #F2613F;"
                          })

    gender = SelectField("",
                         choices=[('', 'Select Gender'), ('Female', 'Female'), ('Male', 'Male'),
                                  ('Others', 'Others'), ('Rather Not Say', 'Rather Not Say')],
                         render_kw={
                             "style": """
                                 width: 100%; 
                                 padding: 12px; 
                                 margin-bottom: 15px; 
                                 border-radius: 5px; 
                                 border: 1px solid #9B3922; 
                                 background-color: #1A1A1A; 
                                 color: #F2613F;
                                 appearance: none; 
                                 -webkit-appearance: none;
                                 -moz-appearance: none;
                                 transition: background-color 0.3s, color 0.3s;
                             """,
                             "class": "gender-select"
                         })
    submit = SubmitField('Submit', render_kw={
        "style": "width: 100%; padding: 12px; margin-top: 15px; "
                 "border-radius: 5px; background-color: #9B3922; color: #F2613F; "
                 "font-size: 16px; cursor: pointer;"
    })
