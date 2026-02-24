from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, IntegerField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(3, 80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(6)])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class CheckoutForm(FlaskForm):
    address = TextAreaField('Shipping Address', validators=[DataRequired(), Length(10)])
    submit = SubmitField('Place Order')


class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(2, 200)])
    description = TextAreaField('Description')
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=0)])
    image_url = StringField('Image URL')
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Product')
