from django.core.management.commands.runserver import Command as RunserverCommand


class Command(RunserverCommand):
    help = "Alias de runserver para desarrollo local."
