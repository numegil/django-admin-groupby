import random
from django.core.management.base import BaseCommand
from cats.models import Cat

class Command(BaseCommand):
    help = 'Generate sample cat data for testing'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=100, help='Number of cats to generate')
        parser.add_argument('--clear', action='store_true', help='Clear existing cats before generating new ones')

    def handle(self, *args, **options):
        count = options['count']
        clear = options['clear']
        
        if clear:
            Cat.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Deleted all existing cats'))
        
        first_names = [
            "Whiskers", "Fluffy", "Luna", "Oliver", "Simba", "Nala", "Leo", "Bella", 
            "Charlie", "Max", "Lucy", "Oreo", "Mittens", "Shadow", "Cleo", "Tiger", 
            "Daisy", "Felix", "Lily", "Oscar", "Zoe", "Smokey", "Milo", "Kitty",
            "Jasper", "Sophie", "Toby", "Chloe", "Mia", "Jack", "Ruby", "Pumpkin",
            "Pepper", "Rocky", "Lola", "Sammy", "Penny", "Finn", "Rosie", "Gus"
        ]
        
        last_names = [
            "Whiskersworth", "Purrson", "Meowington", "Clawford", "Fuzzington",
            "Pawter", "Scratcherson", "Fluffington", "Tabbyton", "Furrington"
        ]
        
        colors = [choice[0] for choice in Cat.COLOR_CHOICES]
        breeds = [choice[0] for choice in Cat.BREED_CHOICES]
        used_names = set()
        cats_created = 0
        
        # Create cats with both first and last names
        for i in range(count):
            # Select a first name
            first_name = random.choice(first_names)
            # Select a last name
            last_name = random.choice(last_names)
            # Combine for full name
            name = f"{first_name} {last_name}"
            
            # Ensure we don't use duplicate names
            while name in used_names:
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                name = f"{first_name} {last_name}"
            
            used_names.add(name)
            
            age = random.randint(1, 15)
            is_vaccinated = random.choice([True, False])
            weight = round(random.uniform(2.0, 10.0), 1)
            color = random.choice(colors)
            breed = random.choice(breeds)
            
            cat = Cat.objects.create(
                name=name,
                age=age,
                is_vaccinated=is_vaccinated,
                weight=weight,
                color=color,
                breed=breed
            )
            cats_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {cats_created} cats.'))