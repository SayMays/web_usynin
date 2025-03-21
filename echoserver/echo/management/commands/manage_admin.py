from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    help = "Управляет ролью пользователя: заменяет текущую роль на admin или возвращает роль user"

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Имя пользователя')
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Если указано, убирает роль admin и возвращает роль user'
        )

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        remove = kwargs['remove']

        try:
            user = User.objects.get(username=username)
            admin_group = Group.objects.get(name='admin')
            user_group = Group.objects.get(name='user')

            if remove:
                if admin_group in user.groups.all():
                    user.groups.remove(admin_group)
                    if user_group not in user.groups.all():
                        user.groups.add(user_group)
                    self.stdout.write(self.style.SUCCESS(f'Роль пользователя {username} изменена на user!'))
                else:
                    self.stdout.write(self.style.WARNING(f'Пользователь {username} не состоит в группе admin.'))
            else:
                if admin_group not in user.groups.all():
                    user.groups.clear()
                    user.groups.add(admin_group)
                    self.stdout.write(self.style.SUCCESS(f'Роль пользователя {username} изменена на admin!'))
                else:
                    self.stdout.write(self.style.WARNING(f'Пользователь {username} уже имеет роль admin.'))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Пользователь {username} не найден.'))
        except Group.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'Группа {e} не найдена.'))