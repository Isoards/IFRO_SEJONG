from django.core.management.base import BaseCommand
from user_auth.models import AdminCode

class Command(BaseCommand):
    help = 'Create admin code for user registration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--code',
            type=str,
            help='Admin code (leave empty for auto-generated)'
        )
        parser.add_argument(
            '--description',
            type=str,
            default='관리자 코드',
            help='Code description'
        )
        parser.add_argument(
            '--max-uses',
            type=int,
            default=1,
            help='Maximum number of uses (default: 1)'
        )
        parser.add_argument(
            '--auto-generate',
            action='store_true',
            help='Enable auto-generation'
        )
        parser.add_argument(
            '--interval-hours',
            type=int,
            default=24,
            help='Generation interval in hours (default: 24)'
        )

    def handle(self, *args, **options):
        code = options['code']
        description = options['description']
        max_uses = options['max_uses']
        auto_generate = options['auto_generate']
        interval_hours = options['interval_hours']

        # 자동 생성 코드인 경우
        if auto_generate:
            code = AdminCode.generate_code()
            description = f"자동 생성 코드 (매 {interval_hours}시간마다 갱신)"
        
        # 코드가 없으면 자동 생성
        if not code:
            code = AdminCode.generate_code()

        # 기존 코드가 있는지 확인
        if AdminCode.objects.filter(code=code).exists():
            self.stdout.write(
                self.style.WARNING(f'Admin code "{code}" already exists!')
            )
            return

        # 새 관리자 코드 생성
        admin_code = AdminCode.objects.create(
            code=code,
            description=description,
            max_uses=max_uses,
            is_active=True,
            auto_generate=auto_generate,
            generation_interval_hours=interval_hours
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created admin code: "{code}"\n'
                f'Description: {description}\n'
                f'Max uses: {max_uses}\n'
                f'Auto generate: {auto_generate}\n'
                f'Interval: {interval_hours} hours'
            )
        ) 