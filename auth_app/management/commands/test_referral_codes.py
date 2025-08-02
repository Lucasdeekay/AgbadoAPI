from django.core.management.base import BaseCommand
from auth_app.utils import generate_unique_referral_code
from auth_app.models import User


class Command(BaseCommand):
    help = 'Test referral code generation functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of referral codes to generate (default: 5)'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        self.stdout.write(
            self.style.SUCCESS(f'Generating {count} unique referral codes...')
        )
        
        generated_codes = []
        
        for i in range(count):
            code = generate_unique_referral_code()
            generated_codes.append(code)
            
            self.stdout.write(
                self.style.SUCCESS(f'Generated code {i+1}: {code}')
            )
        
        # Verify uniqueness
        unique_codes = set(generated_codes)
        if len(unique_codes) == len(generated_codes):
            self.stdout.write(
                self.style.SUCCESS('✅ All codes are unique!')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Duplicate codes found!')
            )
        
        # Verify format
        all_valid = True
        for code in generated_codes:
            if not (len(code) == 8 and code.isupper() and code.isalnum()):
                all_valid = False
                self.stdout.write(
                    self.style.ERROR(f'❌ Invalid format for code: {code}')
                )
        
        if all_valid:
            self.stdout.write(
                self.style.SUCCESS('✅ All codes have correct format (8 chars, uppercase, alphanumeric)!')
            )
        
        # Test with existing users
        if User.objects.exists():
            self.stdout.write(
                self.style.WARNING('Testing with existing users...')
            )
            
            existing_codes = set(User.objects.values_list('referral_code', flat=True))
            existing_codes.discard(None)  # Remove None values
            
            for code in generated_codes:
                if code in existing_codes:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Generated code conflicts with existing user: {code}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Code {code} does not conflict with existing users')
                    )
        
        self.stdout.write(
            self.style.SUCCESS('Referral code generation test completed!')
        ) 