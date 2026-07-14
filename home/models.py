from django.db import models

class Profile(models.Model):
    photo = models.ImageField(upload_to='profile/', blank=True, null=True)

    # Extra CV-only content. Everything else the CV needs (GitHub repos,
    # education) is pulled live from the GitHub API / about.Education, so the
    # "Download CV" button always regenerates a fresh PDF from current data.
    full_name = models.CharField(max_length=120, blank=True, default='Md. Al Fahim Fuyad')
    title = models.CharField(max_length=160, blank=True, default='Data Scientist | ML Engineer | AI Builder')
    location = models.CharField(max_length=120, blank=True, default='Dhaka, Bangladesh')
    summary = models.TextField(
        blank=True,
        help_text="Short professional summary shown at the top of the generated CV.")
    skills = models.TextField(
        blank=True,
        help_text="One category per line, e.g. 'Languages: Python, SQL, JavaScript'.")
    experience = models.TextField(
        blank=True,
        help_text="One entry per line, e.g. 'Role — Organization (Year–Year): what you did'.")
    certifications = models.TextField(
        blank=True,
        help_text="One certification per line. Leave blank to omit this section.")

    def __str__(self):
        return "Profile"