from django.contrib.auth.forms import PasswordChangeForm
from django.utils import timezone
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from .models import AuthUser, Book, Cart, CartItem, Orders, OrderItem, AuthGroup, AuthUserGroups
from .forms import BookForm, CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth import login, logout, update_session_auth_hash
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

def is_admin(user):
    if not user.is_authenticated:
        return False
    try:
        admin_group = AuthGroup.objects.get(name='admin')
        return AuthUserGroups.objects.filter(user_id=user.id, group=admin_group).exists()
    except AuthGroup.DoesNotExist:
        return False


def book_list(request):
    books = Book.objects.all().order_by('book_name')
    paginator = Paginator(books, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'book_list.html', {
        'page_obj': page_obj,
        'is_admin': is_admin(request.user),
        'is_authenticated': request.user.is_authenticated
    })


@login_required
def add_to_cart(request, book_id):
    book = get_object_or_404(Book, book_id=book_id)
    cart, created = Cart.objects.get_or_create(
        user_id=request.user.id,
        defaults={'created_at': timezone.now()}
    )

    cart_item, created = CartItem.objects.get_or_create(
        cart_id=cart.cart_id,
        book_id=book.book_id,
        defaults={'quantity': 1}
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, f'Книга "{book.book_name}" добавлена в корзину')
    return redirect('book_list')


@login_required
def view_cart(request):
    try:
        cart = Cart.objects.get(user_id=request.user.id)
        cart_items = CartItem.objects.filter(cart_id=cart.cart_id).select_related('book')

        items_with_totals = []
        cart_total = 0

        for item in cart_items:
            item_total = round(float(item.book.book_price) * item.quantity, 2)
            items_with_totals.append({
                'item': item,
                'total': item_total,
                'price_per_item': round(float(item.book.book_price), 2)
            })
            cart_total = round(cart_total + item_total, 2)

    except Cart.DoesNotExist:
        items_with_totals = []
        cart_total = 0

    return render(request, 'cart.html', {
        'items_with_totals': items_with_totals,
        'cart_total': cart_total,
        'is_admin': is_admin(request.user)
    })


@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, cart_item_id=cart_item_id, cart__user_id=request.user.id)

    if request.method == 'POST' and 'remove_all' in request.POST:
        cart_item.delete()
        messages.success(request, f'Все {cart_item.quantity} экз. книги удалены')
        return redirect('view_cart')

    if request.method == 'POST' and 'quantity' in request.POST:
        quantity = int(request.POST['quantity'])
        if quantity >= cart_item.quantity:
            cart_item.delete()
            messages.success(request, 'Все экземпляры книги удалены')
        else:
            cart_item.quantity -= quantity
            cart_item.save()
            messages.success(request, f'Удалено {quantity} экз. книги')
        return redirect('view_cart')

    if cart_item.quantity > 1 and not request.GET.get('force_delete'):
        return render(request, 'remove_quantity.html', {
            'cart_item': cart_item,
            'total_price': round(float(cart_item.book.book_price) * cart_item.quantity, 2),
            'range_options': range(1, cart_item.quantity + 1),
            'is_admin': is_admin(request.user)
        })

    cart_item.delete()
    messages.success(request, 'Книга удалена из корзины')
    return redirect('view_cart')


@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user_id=request.user.id)
        cart_items = CartItem.objects.filter(cart_id=cart.cart_id).select_related('book')

        if not cart_items.exists():
            messages.error(request, 'Ваша корзина пуста')
            return redirect('view_cart')

        with transaction.atomic():
            order_total = sum(float(item.book.book_price) * item.quantity for item in cart_items)
            order = Orders.objects.create(
                user_id=request.user.id,
                total_price=order_total,
                status='На рассмотрении',
                created_at=timezone.now()
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order_id=order.order_id,
                    book_id=item.book.book_id,
                    quantity=item.quantity,
                    price=item.book.book_price
                )

            cart_items.delete()

        messages.success(request, f'Заказ #{order.order_id} успешно оформлен')
        return redirect('order_history')

    except Cart.DoesNotExist:
        messages.error(request, 'Ваша корзина пуста')
        return redirect('view_cart')


@login_required
def order_history(request):
    orders = Orders.objects.filter(user_id=request.user.id).order_by('-created_at')
    return render(request, 'order_history.html', {
        'orders': orders,
        'is_admin': is_admin(request.user)
    })


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Orders, order_id=order_id, user_id=request.user.id)
    order_items = OrderItem.objects.filter(order_id=order.order_id).select_related('book')

    items_with_totals = []
    order_calculated_total = 0

    for item in order_items:
        item_total = float(item.price) * item.quantity
        items_with_totals.append({
            'item': item,
            'total': item_total
        })
        order_calculated_total += item_total

    return render(request, 'order_detail.html', {
        'order': order,
        'items_with_totals': items_with_totals,
        'order_calculated_total': order_calculated_total,
        'is_admin': is_admin(request.user)
    })


@login_required
def profile(request):
    user = AuthUser.objects.get(id=request.user.id)

    if request.method == 'POST':
        user.username = request.POST.get('username', user.username)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        messages.success(request, 'Профиль успешно обновлен')
        return redirect('profile')

    return render(request, 'profile.html', {
        'user': user,
        'is_admin': is_admin(request.user)
    })


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Ваш пароль был успешно изменен!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'change_password.html', {
        'form': form,
        'is_admin': is_admin(request.user)
    })