from django.db import models

class Profile(models.Model):
    photo = models.ImageField(upload_to='profile/', blank=True, null=True)

    # Extra CV-only content. Everything else the CV needs (GitHub repos,
    # education) is pulled live from the GitHub API / about.Education, so the
    # "Download CV" button always regenerates a fresh PDF from current data.
    full_name = models.CharField(max_length=120, blank=True, default='Md. Al Fahim Fuyad')
    title = models.CharField(max_length=160, blank=True, default='Data Scientist | ML Engineer | AI Builder')
    location = models.CharField(max_length=120, blank=True, default='Dhaka, Bangladesh')
    phone = models.CharField(max_length=40, blank=True, help_text="Optional. Leave blank to omit from the CV.")
    website = models.CharField(max_length=160, blank=True, help_text="Optional personal site/portfolio URL.")
    summary = models.TextField(
        blank=True,
        help_text="Short professional summary shown at the top of the generated CV.")
    skills = models.TextField(
        blank=True,
        help_text="One category per line, e.g. 'Languages: Python, SQL, JavaScript'. Rendered as pill tags.")
    core_competencies = models.TextField(
        blank=True,
        help_text="One competency per line, e.g. 'Machine Learning & Deep Learning'. Leave blank to omit.")
    experience = models.TextField(
        blank=True,
        help_text=(
            "Blocks separated by a BLANK LINE. First line of each block: "
            "'Role | Organization | Date range'. Following lines are bullet points. Example:\n"
            "AI/ML Engineer (Freelance) | Remote | Jan 2024 – Present\n"
            "Built and deployed end-to-end ML models and data pipelines.\n"
            "\nData Science Intern | ABC Tech Solutions, Dhaka | Jul 2023 – Dec 2023\n"
            "Analyzed large datasets to extract insights."
        ))
    certifications = models.TextField(
        blank=True,
        help_text="One certification per line. Leave blank to omit this section.")
    achievements = models.TextField(
        blank=True,
        help_text="One achievement per line. Leave blank to omit this section.")
    languages = models.TextField(
        blank=True,
        help_text="One per line: 'Language: Level' e.g. 'English: Professional'. Level can be "
                   "Native/Fluent/Professional/Intermediate/Basic.")
    interests = models.TextField(
        blank=True,
        help_text="Comma or line separated interests, e.g. 'AI Research, Open Source, Problem Solving'.")
    quote = models.CharField(
        max_length=200, blank=True,
        default="Code is like humor. When you have to explain it, it's bad.",
        help_text="Short quote shown in the CV footer.")

    def __str__(self):
        return "Profile"