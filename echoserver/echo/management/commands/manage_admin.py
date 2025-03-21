from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    help = "Управляет правами администратора: добавляет или удаляет пользователя из группы admin"

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Имя пользователя')
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Если указано, удаляет пользователя из группы admin вместо добавления'
        )

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        remove = kwargs['remove']

        try:
            user = User.objects.get(username=username)
            admin_group = Group.objects.get(name='admin')

            if remove:
                if admin_group in user.groups.all():
                    user.groups.remove(admin_group)
                    self.stdout.write(self.style.SUCCESS(f'Пользователь {username} успешно удален из группы admin!'))
                else:
                    self.stdout.write(self.style.WARNING(f'Пользователь {username} не состоит в группе admin.'))
            else:
                if admin_group not in user.groups.all():
                    user.groups.add(admin_group)
                    self.stdout.write(self.style.SUCCESS(f'Пользователь {username} успешно добавлен в группу admin!'))
                else:
                    self.stdout.write(self.style.WARNING(f'Пользователь {username} уже состоит в группе admin.'))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Пользователь {username} не найден.'))
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR('Группа admin не найдена.'))