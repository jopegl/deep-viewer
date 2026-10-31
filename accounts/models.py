from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        RESEARCHER = "researcher", "Pesquisador"
        ADVISOR = "advisor", "Orientador"

    email = models.EmailField("e-mail", unique=True)
    institution = models.CharField("instituição", max_length=150, blank=True, default="")
    research_area = models.CharField("área de pesquisa", max_length=150, blank=True, default="")
    role = models.CharField("papel", max_length=20, choices=Role.choices, default=Role.RESEARCHER)