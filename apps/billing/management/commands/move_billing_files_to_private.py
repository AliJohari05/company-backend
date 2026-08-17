import filecmp
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        'Move contract and payment receipt files from public MEDIA_ROOT '
        'to PRIVATE_MEDIA_ROOT.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show files that would be moved without changing them.',
        )

    def handle(self, *args, **options):
        public_root = Path(settings.MEDIA_ROOT).resolve()
        private_root = Path(settings.PRIVATE_MEDIA_ROOT).resolve()
        dry_run = options['dry_run']
        moved_count = 0

        if public_root == private_root:
            raise CommandError(
                'MEDIA_ROOT and PRIVATE_MEDIA_ROOT must be different directories.'
            )

        for directory_name in ('contracts', 'receipts'):
            source_directory = (public_root / directory_name).resolve()
            destination_directory = (private_root / directory_name).resolve()

            self._ensure_inside(source_directory, public_root)
            self._ensure_inside(destination_directory, private_root)

            if not source_directory.exists():
                continue

            for source_path in source_directory.rglob('*'):
                if not source_path.is_file():
                    continue

                relative_path = source_path.relative_to(public_root)
                destination_path = (private_root / relative_path).resolve()
                self._ensure_inside(destination_path, private_root)

                if destination_path.exists():
                    if not filecmp.cmp(
                        source_path,
                        destination_path,
                        shallow=False,
                    ):
                        raise CommandError(
                            f'Destination already exists with different content: '
                            f'{destination_path}'
                        )

                    self.stdout.write(
                        f'Already copied, removing public duplicate: {relative_path}'
                    )
                    if not dry_run:
                        source_path.unlink()
                    moved_count += 1
                    continue

                self.stdout.write(f'Moving: {relative_path}')
                if not dry_run:
                    destination_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source_path), str(destination_path))
                moved_count += 1

        if not dry_run:
            self._remove_empty_directories(public_root / 'contracts')
            self._remove_empty_directories(public_root / 'receipts')

        action = 'Would move' if dry_run else 'Moved'
        self.stdout.write(self.style.SUCCESS(f'{action} {moved_count} file(s).'))

    @staticmethod
    def _ensure_inside(path, root):
        try:
            path.relative_to(root)
        except ValueError as error:
            raise CommandError(
                f'Unsafe path outside configured storage root: {path}'
            ) from error

    @staticmethod
    def _remove_empty_directories(directory):
        if not directory.exists():
            return

        directories = sorted(
            (path for path in directory.rglob('*') if path.is_dir()),
            reverse=True,
        )
        for path in directories:
            try:
                path.rmdir()
            except OSError:
                pass

        try:
            directory.rmdir()
        except OSError:
            pass
