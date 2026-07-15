from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'full_name', 'title')
    fieldsets = (
        ('Photo', {'fields': ('photo',)}),
        ('Identity', {
            'fields': ('full_name', 'title', 'location', 'phone', 'website'),
        }),
        ('CV content', {
            'fields': (
                'summary', 'skills', 'core_competencies', 'experience',
                'certifications', 'achievements', 'languages', 'interests', 'quote',
            ),
            'description': 'Everything here feeds the auto-generated "Download CV" PDF. '
                            'GitHub repos and education are pulled in live and need no editing here. '
                            'Leave any field blank to omit that section from the CV.',
        }),
    )