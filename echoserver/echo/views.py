from django.db.models import Q
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from .models import AuthUser, Book, Cart, CartItem, Orders, OrderItem, AuthGroup, AuthUserGroups
from .forms import BookForm, CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth import login, update_session_auth_hash, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import Group


def is_admin(user):
    return user.is_authenticated and user.groups.filter(name='admin').exists()


def book_list(request):
    books = Book.objects.all()

    search = request.GET.get('search', '')
    book_name = request.GET.get('book_name', '')
    author = request.GET.get('author', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    in_stock = request.GET.get('in_stock', '')
    sort = request.GET.get('sort', '')

    if search:
        books = books.filter(
            Q(book_name__icontains=search) |
            Q(author__icontains=search)
        )

    if book_name:
        books = books.filter(book_name__icontains=book_name)
    if author:
        books = books.filter(author__icontains=author)
    if price_min:
        try:
            books = books.filter(book_price__gte=float(price_min))
        except ValueError:
            pass
    if price_max:
        try:
            books = books.filter(book_price__lte=float(price_max))
        except ValueError:
            pass
    if in_stock:
        books = books.filter(book_count__gt=0)

    if sort == 'name_asc':
        books = books.order_by('book_name')
    elif sort == 'name_desc':
        books = books.order_by('-book_name')
    elif sort == 'price_asc':
        books = books.order_by('book_price')
    elif sort == 'price_desc':
        books = books.order_by('-book_price')
    else:
        books = books.order_by('book_name')  # Сортировка по умолчанию

    paginator = Paginator(books, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'book_name': book_name,
        'author': author,
        'price_min': price_min,
        'price_max': price_max,
        'sort': sort,
        'is_admin': request.user.groups.filter(name='admin').exists() if request.user.is_authenticated else False,
        'is_authenticated': request.user.is_authenticated,
    }
    return render(request, 'book_list.html', context)


@login_required
@user_passes_test(is_admin)
def add_book(request):
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


@login_required
def add_to_cart(request, book_id):
    book = get_object_or_404(Book, book_id=book_id)

    with transaction.atomic():
        book = Book.objects.select_for_update().get(book_id=book_id)

        if book.book_count <= 0:
            return JsonResponse({
                'status': 'error',
                'message': 'Книга закончилась на складе',
                'new_count': book.book_count
            }, status=400)

        book.book_count -= 1
        book.save()

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

    return JsonResponse({
        'status': 'success',
        'message': 'Книга добавлена в корзину',
        'new_count': book.book_count
    })


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

    if request.method == 'POST':
        with transaction.atomic():
            book = Book.objects.select_for_update().get(book_id=cart_item.book.book_id)
            quantity_to_remove = 1

            if 'remove_all' in request.POST:
                quantity_to_remove = cart_item.quantity
            elif 'quantity' in request.POST:
                try:
                    quantity_to_remove = int(request.POST['quantity'])
                    if quantity_to_remove < 1 or quantity_to_remove > cart_item.quantity:
                        messages.error(request, 'Недопустимое количество для удаления')
                        return redirect('view_cart')
                except ValueError:
                    messages.error(request, 'Недопустимое значение количества')
                    return redirect('view_cart')

            book.book_count += quantity_to_remove
            book.save()

            if quantity_to_remove >= cart_item.quantity:
                cart_item.delete()
            else:
                cart_item.quantity -= quantity_to_remove
                cart_item.save()

        messages.success(request, f'Удалено {quantity_to_remove} экз. книги')
        return redirect('view_cart')

    range_options = range(1, cart_item.quantity + 1)
    total_price = cart_item.quantity * cart_item.book.book_price

    return render(request, 'remove_quantity.html', {
        'cart_item': cart_item,
        'range_options': range_options,
        'total_price': total_price,
        'is_admin': is_admin(request.user)
    })


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


@login_required
def clear_cart(request):
    try:
        cart = Cart.objects.get(user_id=request.user.id)
        with transaction.atomic():
            cart_items = CartItem.objects.filter(cart_id=cart.cart_id).select_related('book')
            book_ids = [item.book.book_id for item in cart_items]
            books = Book.objects.select_for_update().filter(book_id__in=book_ids)
            book_dict = {book.book_id: book for book in books}

            for item in cart_items:
                book = book_dict.get(item.book.book_id)
                book.book_count += item.quantity
                book.save()

            cart_items.delete()

        messages.success(request, 'Корзина полностью очищена')
    except Cart.DoesNotExist:
        messages.error(request, 'Корзина уже пуста')

    return redirect('view_cart')


def check_email(request):
    email = request.GET.get('email', '')
    exists = AuthUser.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})


def check_username(request):
    username = request.GET.get('username', '')
    exists = AuthUser.objects.filter(username=username).exists()
    return JsonResponse({'exists': exists})