import filecmp
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        'Move project and ticket attachments from public MEDIA_ROOT '
        'to PRIVATE_MEDIA_ROOT.'
    )

    directories = (
        'project_attachments',
        'tickets/attachments',
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
                'MEDIA_ROOT and PRIVATE_MEDIA_ROOT must be different.'
            )

        for directory_name in self.directories:
            source_directory = (public_root / directory_name).resolve()
            self._ensure_inside(source_directory, public_root)
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
                            'Destination exists with different content: '
                            f'{destination_path}'
                        )
                    self.stdout.write(
                        f'Already copied, removing public duplicate: '
                        f'{relative_path}'
                    )
                    if not dry_run:
                        source_path.unlink()
                    moved_count += 1
                    continue

                self.stdout.write(f'Moving: {relative_path}')
                if not dry_run:
                    destination_path.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )
                    shutil.move(str(source_path), str(destination_path))
                moved_count += 1

        action = 'Would move' if dry_run else 'Moved'
        self.stdout.write(
            self.style.SUCCESS(f'{action} {moved_count} file(s).')
        )

    @staticmethod
    def _ensure_inside(path, root):
        try:
            path.relative_to(root)
        except ValueError as error:
            raise CommandError(
                f'Unsafe path outside configured storage root: {path}'
            ) from error
