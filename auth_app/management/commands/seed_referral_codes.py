import secrets
import string
from django.core.management.base import BaseCommand
from django.db import transaction
from auth_app.models import User  # adjust import if User lives elsewhere


def _generate_code(length=8) -> str:
    """
    Generate an URL-safe random code of *length* characters.
    The alphabet avoids ambiguous characters (0/O, 1/l/I).
    """
    alphabet = string.ascii_uppercase + string.digits
    alphabet = alphabet.translate({ord(c): None for c in "0O1lI"})
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
    help = "Generate referral codes for existing users that do not yet have one."

    def add_arguments(self, parser):
        # Optional argument: length of the generated code
        parser.add_argument(
            "--length",
            type=int,
            default=8,
            help="Length of the referral code to generate (default 8).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        length = max(4, options["length"])
        users_without_code = User.objects.filter(referral_code__isnull=True)

        if not users_without_code.exists():
            self.stdout.write(self.style.NOTICE("No users need a referral code."))
            return

        updated = 0
        for user in users_without_code.iterator():
            while True:  # keep trying until we have a unique code
                code = _generate_code(length)
                if not User.objects.filter(referral_code=code).exists():
                    user.referral_code = code
                    user.save(update_fields=["referral_code"])
                    updated += 1
                    break

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully generated referral codes for {updated} user(s)."
            )
        )
