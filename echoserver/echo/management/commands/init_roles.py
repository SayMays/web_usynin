from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from echo.models import Book


class Command(BaseCommand):
    help = "Создает группы пользователей и назначает им разрешения"

    def handle(self, *args, **kwargs):
        user_group, _ = Group.objects.get_or_create(name="user")
        admin_group, _ = Group.objects.get_or_create(name="admin")

        content_type = ContentType.objects.get_for_model(Book)
        permissions = Permission.objects.filter(content_type=content_type)

        user_perms = permissions.filter(codename__in=["view_book", "add_book"])
        admin_perms = permissions

        user_group.permissions.set(user_perms)
        admin_group.permissions.set(admin_perms)

        self.stdout.write(self.style.SUCCESS("Группы и права успешно созданы!"))
