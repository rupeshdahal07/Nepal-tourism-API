from django.core.management.base import BaseCommand
from api.services.weather import WeatherService

class Command(BaseCommand):
    help = 'Update weather data for all tracked locations'

    def handle(self, *args, **options):
        self.stdout.write('Updating weather data...')
        WeatherService.update_all_locations()
        self.stdout.write(self.style.SUCCESS('Weather data updated successfully'))