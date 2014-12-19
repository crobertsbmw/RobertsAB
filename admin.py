from djangoAB.models import Test, Experiment
from django.contrib import admin

class TestInline(admin.StackedInline):
    model = Test

class ExperimentAdmin(admin.ModelAdmin):
    inlines = [TestInline]
 

admin.site.register(Test)
admin.site.register(Experiment, ExperimentAdmin)
