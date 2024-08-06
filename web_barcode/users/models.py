from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models


class InnotreidUser(AbstractUser):
    """
    Своя модель пользователя для проекта.
    Всегда в проекте переопределять модели пользователя,
    чтобы была возможность без проблем добавлять новые поля
    """
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        verbose_name="username",
        max_length=150,
        unique=True,
        help_text=(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": ("A user with that username already exists."),
        },
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=150,
        blank=True)
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=150,
        blank=True)
    password = models.CharField(
        verbose_name='Пароль',
        max_length=150,
        help_text=('Обязательно для заполнения.Максимум 150 символов.')
    )
    tg_chat_id = models.CharField(
        verbose_name="телеграм chat ID",
        max_length=20,
        blank=True)
    email = models.EmailField(
        verbose_name="email адрес",
        blank=True)

    is_staff = models.BooleanField(
        verbose_name="staff status",
        default=False,
        help_text=("Designates whether the user can log into this admin site."),
    )

    def __str__(self):
        return f'{self.username}'

    class Meta:
        app_label = 'users'
        db_table = 'users_innotreiduser'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


User = get_user_model()


class CustomUserBackend:

    def authenticate(self, request, username=None, password=None):
        try:
            user = User.objects.get(username=username)
            if not user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
