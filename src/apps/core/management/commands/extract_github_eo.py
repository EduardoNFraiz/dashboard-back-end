"""Django management command to extract GitHub data into Django models.

Usage:
    python manage.py extract_github_eo --org <organization> --repo <repository> --token <github_token>
"""

from django.core.management.base import BaseCommand, CommandError
from apps.core.extract_github.extract_eo_django import ExtractEODjango
import os


class Command(BaseCommand):
    help = 'Extract GitHub teams, projects, and members data into Django models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org',
            type=str,
            help='GitHub organization name',
            required=False,
        )
        parser.add_argument(
            '--repo',
            type=str,
            help='GitHub repository in format "org/repo"',
            required=False,
        )
        parser.add_argument(
            '--token',
            type=str,
            help='GitHub personal access token',
            required=False,
        )
        parser.add_argument(
            '--use-env',
            action='store_true',
            help='Use environment variables for configuration',
        )
        parser.add_argument(
            '--streams',
            type=str,
            help='Comma-separated list of streams to extract (projects_v2,teams,team_members)',
            default='projects_v2,teams,team_members'
        )

    def handle(self, *args, **options):
        """Execute the extraction command."""
        
        # Get configuration from arguments or environment
        if options['use_env']:
            organization = os.getenv('GITHUB_ORGANIZATION') or os.getenv('ORGANIZATION')
            repository = os.getenv('GITHUB_REPOSITORY') or os.getenv('REPOSITORIES')
            token = os.getenv('GITHUB_TOKEN')
        else:
            organization = options.get('org')
            repository = options.get('repo')
            token = options.get('token')
        
        # Validate required parameters
        if not organization:
            raise CommandError('Organization is required. Use --org or set GITHUB_ORGANIZATION env var.')
        if not repository:
            raise CommandError('Repository is required. Use --repo or set GITHUB_REPOSITORY env var.')
        if not token:
            raise CommandError('GitHub token is required. Use --token or set GITHUB_TOKEN env var.')
        
        self.stdout.write(self.style.SUCCESS(f'Starting extraction for {organization}/{repository}...'))
        
        try:
            # Initialize and run extractor
            extractor = ExtractEODjango(
                organization=organization,
                secret=token,
                repository=repository
            )
            
            # Allow stream customization
            if options.get('streams'):
                extractor.streams = options['streams'].split(',')
            
            result = extractor.run()
            
            if result['status'] == 'success':
                self.stdout.write(self.style.SUCCESS('✅ Extraction completed successfully!'))
                self.stdout.write(self.style.SUCCESS(f'📊 Statistics:'))
                for key, value in result['statistics'].items():
                    self.stdout.write(f'  - {key}: {value}')
            else:
                self.stdout.write(self.style.ERROR(f'❌ Extraction failed: {result["message"]}'))
                
        except Exception as e:
            raise CommandError(f'Extraction failed with error: {str(e)}')
