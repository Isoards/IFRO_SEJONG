from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Delete users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Specific username to delete'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Specific email to delete'
        )
        parser.add_argument(
            '--role',
            type=str,
            choices=['admin', 'operator'],
            help='Delete users with specific role'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Delete all users (except superusers)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force delete without confirmation'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        role = options['role']
        delete_all = options['all']
        force = options['force']

        if username:
            # 특정 사용자명으로 삭제
            try:
                user = User.objects.get(username=username)
                if user.is_superuser:
                    self.stdout.write(
                        self.style.ERROR(f'슈퍼유저 "{username}"는 삭제할 수 없습니다.')
                    )
                    return
                
                if not force:
                    confirm = input(f'정말로 사용자 "{username}"를 삭제하시겠습니까? (y/N): ')
                    if confirm.lower() != 'y':
                        self.stdout.write('삭제가 취소되었습니다.')
                        return
                
                user.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'사용자 "{username}"가 삭제되었습니다.')
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'사용자 "{username}"를 찾을 수 없습니다.')
                )

        elif email:
            # 특정 이메일로 삭제
            try:
                user = User.objects.get(email=email)
                if user.is_superuser:
                    self.stdout.write(
                        self.style.ERROR(f'슈퍼유저 "{email}"는 삭제할 수 없습니다.')
                    )
                    return
                
                if not force:
                    confirm = input(f'정말로 사용자 "{email}"를 삭제하시겠습니까? (y/N): ')
                    if confirm.lower() != 'y':
                        self.stdout.write('삭제가 취소되었습니다.')
                        return
                
                user.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'사용자 "{email}"가 삭제되었습니다.')
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'사용자 "{email}"를 찾을 수 없습니다.')
                )

        elif role:
            # 특정 역할의 사용자들 삭제
            users = User.objects.filter(role=role, is_superuser=False)
            if not users.exists():
                self.stdout.write(f'삭제할 {role} 역할의 사용자가 없습니다.')
                return

            if not force:
                confirm = input(f'{users.count()}명의 {role} 역할 사용자를 삭제하시겠습니까? (y/N): ')
                if confirm.lower() != 'y':
                    self.stdout.write('삭제가 취소되었습니다.')
                    return

            count = users.count()
            users.delete()
            self.stdout.write(
                self.style.SUCCESS(f'{count}명의 {role} 역할 사용자가 삭제되었습니다.')
            )

        elif delete_all:
            # 모든 일반 사용자 삭제 (슈퍼유저 제외)
            users = User.objects.filter(is_superuser=False)
            if not users.exists():
                self.stdout.write('삭제할 일반 사용자가 없습니다.')
                return

            if not force:
                confirm = input(f'{users.count()}명의 모든 일반 사용자를 삭제하시겠습니까? (y/N): ')
                if confirm.lower() != 'y':
                    self.stdout.write('삭제가 취소되었습니다.')
                    return

            count = users.count()
            users.delete()
            self.stdout.write(
                self.style.SUCCESS(f'{count}명의 모든 일반 사용자가 삭제되었습니다.')
            )

        else:
            self.stdout.write(
                self.style.WARNING(
                    '사용법:\n'
                    '  --username USERNAME: 특정 사용자명 삭제\n'
                    '  --email EMAIL: 특정 이메일 삭제\n'
                    '  --role ROLE: 특정 역할 사용자들 삭제\n'
                    '  --all: 모든 일반 사용자 삭제\n'
                    '  --force: 확인 없이 삭제'
                )
            ) 