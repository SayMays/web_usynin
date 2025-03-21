from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from .models import Book
from .forms import BookForm, CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import Group

def is_admin(user):
    return user.is_authenticated and user.groups.filter(name='admin').exists()


def book_list(request):
    books = Book.objects.all().order_by('book_name')
    paginator = Paginator(books, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'book_list.html', {
        'page_obj': page_obj,
        'is_admin': request.user.is_authenticated and is_admin(request.user),
        'is_authenticated': request.user.is_authenticated
    })


@login_required
def add_book(request):
    if not request.user.groups.filter(name__in=['user', 'admin']).exists():
        messages.error(request, 'У вас нет прав для добавления книг')
        return redirect('book_list')

    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Книга успешно добавлена')
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'book_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def edit_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, 'Книга успешно отредактирована')
            return redirect('book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'book_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def delete_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    book.delete()
    messages.success(request, 'Книга успешно удалена')
    return redirect('book_list')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_group = Group.objects.get(name='user')
            user.groups.add(user_group)
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно')
            return redirect('book_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Вы успешно вошли в систему')
            return redirect('book_list')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'login.html', {'form': form})


@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'Вы вышли из системы')
    return redirect('book_list')