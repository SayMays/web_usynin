from django import forms
from .models import Book

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['book_name', 'author', 'book_price']
        labels = {
            'book_name': 'Название',
            'author': 'Автор',
            'book_price': 'Цена (в руб.)'
        }
