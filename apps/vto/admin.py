from django.contrib import admin

from .models import EventoVTO


@admin.register(EventoVTO)
class EventoVTOAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'producto', 'timestamp')
    list_filter = ('timestamp',)
    date_hierarchy = 'timestamp'
    raw_id_fields = ('producto',)
