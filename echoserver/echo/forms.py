from django import forms
from .models import Book
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['book_name', 'author', 'book_price']
        labels = {
            'book_name': 'Название',
            'author': 'Автор',
            'book_price': 'Цена (в руб.)'
        }

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'email', 'password1', 'password2')
        labels = {
            'username': 'Логин',
            'first_name': 'Имя',
            'email': 'Почта',
            'password1': 'Пароль',
            'password2': 'Подтверждение пароля',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Логин'
        self.fields['username'].help_text = ''
        self.fields['first_name'].label = 'Имя'
        self.fields['first_name'].help_text = ''
        self.fields['first_name'].required = False  # Имя необязательное
        self.fields['email'].label = 'Почта'
        self.fields['email'].help_text = ''
        self.fields['email'].required = True  # Почта обязательная
        self.fields['password1'].label = 'Пароль'
        self.fields['password1'].help_text = ''
        self.fields['password2'].label = 'Подтверждение пароля'
        self.fields['password2'].help_text = ''

        self.error_messages.update({
            'password_mismatch': 'Пароли не совпадают.',
        })

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            try:
                validate_password(password1, self.instance)
            except ValidationError as error:
                translated_errors = []
                for message in error.messages:
                    if message == "This password is too short. It must contain at least 8 characters.":
                        translated_errors.append("Пароль слишком короткий. Он должен содержать как минимум 8 символов.")
                    elif message == "This password is too common.":
                        translated_errors.append("Этот пароль слишком часто используется.")
                    elif message == "This password is entirely numeric.":
                        translated_errors.append("Пароль не может состоять только из цифр.")
                    elif message == "The password is too similar to the username.":
                        translated_errors.append("Пароль слишком похож на ваш логин.")
                    else:
                        translated_errors.append(message)
                raise ValidationError(translated_errors)
        return password1

    def clean(self):
        cleaned_data = super().clean()
        if 'password1' in self.errors:
            del self.errors['password1']
        return cleaned_data

class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ('username', 'password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Логин'
        self.fields['password'].label = 'Пароль'
        self.error_messages['invalid_login'] = (
            'Пожалуйста, введите правильный логин и пароль. '
            'Обратите внимание, что оба поля чувствительны к регистру.'
        )

    def clean(self):
        cleaned_data = super().clean()
        if self.non_field_errors():
            self._errors['__all__'] = self.error_messages['invalid_login']
        return cleaned_data