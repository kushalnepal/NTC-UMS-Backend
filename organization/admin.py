from django.contrib import admin
from .models import Domain, Organization, Department, Wing, Role, Membership

admin.site.register(Domain)
admin.site.register(Organization)
admin.site.register(Department)
admin.site.register(Wing)
admin.site.register(Role)
admin.site.register(Membership)
