from django.db import models

class Cat(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    is_vaccinated = models.BooleanField(null=True, blank=True, default=None)
    weight = models.FloatField()
    adoption_date = models.DateField(null=True, blank=True)
    
    COLOR_CHOICES = [
        ('BLK', 'Black'),
        ('WHT', 'White'),
        ('GRY', 'Gray'),
        ('BRN', 'Brown'),
        ('ORG', 'Orange'),
    ]
    color = models.CharField(max_length=3, choices=COLOR_CHOICES, default='BLK')
    
    BREED_CHOICES = [
        ('PER', 'Persian'),
        ('SIA', 'Siamese'),
        ('BSH', 'British Shorthair'),
        ('BEN', 'Bengal'),
        ('RAG', 'Ragdoll'),
        ('SPH', 'Sphynx'),
        ('MCO', 'Maine Coon'),
        ('ABY', 'Abyssinian'),
    ]
    breed = models.CharField(max_length=3, choices=BREED_CHOICES, default='PER')
    
    def __str__(self):
        return self.name