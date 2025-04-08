from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Создает нового пользователя в таблице auth_user через консоль'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Имя пользователя')
        parser.add_argument('password', type=str, help='Пароль пользователя')

        parser.add_argument('--first_name', type=str, help='Имя пользователя (можно с фамилией через пробел)',
                            default='')
        parser.add_argument('--email', type=str, help='Электронная почта пользователя', default='')
        parser.add_argument('--is_staff', action='store_true', help='Дать пользователю права персонала (is_staff=True)')
        parser.add_argument('--is_superuser', action='store_true',
                            help='Сделать пользователя суперпользователем (is_superuser=True)')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        first_name = options['first_name']
        email = options['email']
        is_staff = options['is_staff']
        is_superuser = options['is_superuser']

        try:
            if User.objects.filter(username=username).exists():
                raise CommandError(f"Пользователь с именем '{username}' уже существует.")

            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name='',
                is_staff=is_staff,
                is_superuser=is_superuser
            )

            self.stdout.write(self.style.SUCCESS(
                f"Пользователь '{username}' успешно создан."
            ))

        except Exception as e:
            raise CommandError(f"Ошибка при создании пользователя: {str(e)}")