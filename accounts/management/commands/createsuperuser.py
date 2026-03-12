from django.contrib.auth.management.commands.createsuperuser import Command as BaseCommand
from django.core.management.base import CommandError
from django.db import transaction
from accounts.models import User


class Command(BaseCommand):
    help = 'Create a superuser with custom identifier (username, email, or phone)'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--identifier',
            type=str,
            help='Identifier for the superuser (username, email, or phone)',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the superuser',
        )

    def handle(self, *args, **options):
        identifier = options.get('identifier')

        if identifier:
            # Use custom logic for identifier-based creation
            password = options.get('password')

            if not password:
                raise CommandError('--password is required when using --identifier')

            try:
                with transaction.atomic():
                    user = User.objects.create_superuser(
                        identifier=identifier,
                        password=password,
                    )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully created superuser with identifier: {identifier}'
                        )
                    )
            except Exception as e:
                raise CommandError(f'Failed to create superuser: {str(e)}')
        else:
            # Fall back to default behavior
            super().handle(*args, **options)