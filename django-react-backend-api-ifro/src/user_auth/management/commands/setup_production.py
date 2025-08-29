from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from user_auth.models import AdminCode
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup production environment with superuser and admin codes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--superuser-username',
            type=str,
            default='admin',
            help='Superuser username (default: admin)'
        )
        parser.add_argument(
            '--superuser-email',
            type=str,
            required=True,
            help='Superuser email'
        )
        parser.add_argument(
            '--superuser-password',
            type=str,
            required=True,
            help='Superuser password'
        )
        parser.add_argument(
            '--create-auto-admin-code',
            action='store_true',
            help='Create auto-generating admin code'
        )

    def handle(self, *args, **options):
        username = options['superuser_username']
        email = options['superuser_email']
        password = options['superuser_password']
        create_auto_code = options['create_auto_admin_code']

        # 슈퍼유저 생성
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                name='System Administrator'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Superuser "{username}" created successfully!')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Superuser "{username}" already exists!')
            )

        # 자동 생성 관리자 코드 생성
        if create_auto_code:
            if not AdminCode.objects.filter(auto_generate=True).exists():
                auto_code = AdminCode.objects.create(
                    code=AdminCode.generate_code(),
                    description="프로덕션 자동 생성 관리자 코드 (사용 즉시 갱신, 미사용 시 24시간마다 갱신)",
                    max_uses=1,
                    is_active=True,
                    auto_generate=True,
                    generation_interval_hours=24
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Auto-generating admin code created: "{auto_code.code}"'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Auto-generating admin code already exists!')
                )

        self.stdout.write(
            self.style.SUCCESS('Production setup completed!')
        ) 