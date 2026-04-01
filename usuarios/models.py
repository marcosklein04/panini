from __future__ import annotations

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from core.modelos import ModeloBaseUUID


class GestorUsuario(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("El correo electronico es obligatorio.")
        email = self.normalize_email(email)
        usuario = self.model(email=email, **extra_fields)
        if password:
            usuario.set_password(password)
        else:
            usuario.set_unusable_password()
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("nombre", "Administrador")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class Usuario(ModeloBaseUUID, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name="Correo electronico")
    nombre = models.CharField(max_length=150, verbose_name="Nombre")
    is_staff = models.BooleanField(default=False, verbose_name="Es personal")
    is_active = models.BooleanField(default=True, verbose_name="Esta activo")

    objects = GestorUsuario()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre"]

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["email"]

    def __str__(self) -> str:
        return self.email
