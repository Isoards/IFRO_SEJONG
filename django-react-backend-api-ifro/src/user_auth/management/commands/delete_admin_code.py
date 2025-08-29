from django.core.management.base import BaseCommand
from user_auth.models import AdminCode

class Command(BaseCommand):
    help = 'Delete admin codes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--code',
            type=str,
            help='Specific admin code to delete'
        )
        parser.add_argument(
            '--auto-generate',
            action='store_true',
            help='Delete auto-generating codes only'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Delete all admin codes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force delete without confirmation'
        )

    def handle(self, *args, **options):
        code = options['code']
        auto_generate = options['auto_generate']
        delete_all = options['all']
        force = options['force']

        if code:
            # 특정 코드 삭제
            try:
                admin_code = AdminCode.objects.get(code=code)
                if not force:
                    confirm = input(f'정말로 코드 "{code}"를 삭제하시겠습니까? (y/N): ')
                    if confirm.lower() != 'y':
                        self.stdout.write('삭제가 취소되었습니다.')
                        return
                
                admin_code.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'코드 "{code}"가 삭제되었습니다.')
                )
            except AdminCode.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'코드 "{code}"를 찾을 수 없습니다.')
                )

        elif auto_generate:
            # 자동 생성 코드만 삭제
            auto_codes = AdminCode.objects.filter(auto_generate=True)
            if not auto_codes.exists():
                self.stdout.write('삭제할 자동 생성 코드가 없습니다.')
                return

            if not force:
                confirm = input(f'{auto_codes.count()}개의 자동 생성 코드를 삭제하시겠습니까? (y/N): ')
                if confirm.lower() != 'y':
                    self.stdout.write('삭제가 취소되었습니다.')
                    return

            count = auto_codes.count()
            auto_codes.delete()
            self.stdout.write(
                self.style.SUCCESS(f'{count}개의 자동 생성 코드가 삭제되었습니다.')
            )

        elif delete_all:
            # 모든 코드 삭제
            all_codes = AdminCode.objects.all()
            if not all_codes.exists():
                self.stdout.write('삭제할 관리자 코드가 없습니다.')
                return

            if not force:
                confirm = input(f'{all_codes.count()}개의 모든 관리자 코드를 삭제하시겠습니까? (y/N): ')
                if confirm.lower() != 'y':
                    self.stdout.write('삭제가 취소되었습니다.')
                    return

            count = all_codes.count()
            all_codes.delete()
            self.stdout.write(
                self.style.SUCCESS(f'{count}개의 모든 관리자 코드가 삭제되었습니다.')
            )

        else:
            self.stdout.write(
                self.style.WARNING(
                    '사용법:\n'
                    '  --code CODE: 특정 코드 삭제\n'
                    '  --auto-generate: 자동 생성 코드만 삭제\n'
                    '  --all: 모든 코드 삭제\n'
                    '  --force: 확인 없이 삭제'
                )
            ) 