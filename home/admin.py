from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'full_name', 'title')
    fieldsets = (
        ('Photo', {'fields': ('photo',)}),
        ('CV content', {
            'fields': ('full_name', 'title', 'location', 'summary', 'skills', 'experience', 'certifications'),
            'description': 'Everything here feeds the auto-generated "Download CV" PDF. '
                            'GitHub repos and education are pulled in live and need no editing here.',
        }),
    )