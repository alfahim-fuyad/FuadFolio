from django.db import models

class Profile(models.Model):
    photo = models.ImageField(upload_to='profile/')
    resume = models.FileField(upload_to='resume/', blank=True, null=True,
                               help_text="Upload the CV/resume PDF served by the Download CV button.")

    def __str__(self):
        return "Profile"