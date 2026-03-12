from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from accounts.models import User
from organization.models import Domain, Organization, Department, Wing, Role, Membership

class Command(BaseCommand):
    help = 'Seed the database with sample data'

    def handle(self, *args, **options):
        # Create roles
        admin_role, _ = Role.objects.get_or_create(name='Admin', defaults={'permissions': ['read', 'write', 'delete']})
        user_role, _ = Role.objects.get_or_create(name='User', defaults={'permissions': ['read']})

        # Create domains
        domain1, _ = Domain.objects.get_or_create(name='Nepal Telecom')
        domain2, _ = Domain.objects.get_or_create(name='NTC Subsidiaries')

        # Create organizations
        org1, _ = Organization.objects.get_or_create(domain=domain1, name='Technical Division')
        org2, _ = Organization.objects.get_or_create(domain=domain1, name='Commercial Division')
        org3, _ = Organization.objects.get_or_create(domain=domain2, name='Data Center Org')

        # Create departments
        dept1, _ = Department.objects.get_or_create(organization=org1, name='Fiber Department')
        dept2, _ = Department.objects.get_or_create(organization=org1, name='IT Department')
        dept3, _ = Department.objects.get_or_create(organization=org2, name='Sales Department')
        dept4, _ = Department.objects.get_or_create(organization=org3, name='Cloud Department')

        # Create wings
        wing1, _ = Wing.objects.get_or_create(department=dept1, name='Installation Wing')
        wing2, _ = Wing.objects.get_or_create(department=dept1, name='Maintenance Wing')
        wing3, _ = Wing.objects.get_or_create(department=dept2, name='Security Wing')
        wing4, _ = Wing.objects.get_or_create(department=dept2, name='DevOps Wing')
        wing5, _ = Wing.objects.get_or_create(department=dept3, name='Retail Wing')
        wing6, _ = Wing.objects.get_or_create(department=dept4, name='Infrastructure Wing')

        # Create users (keep only essential ones)
        user1, _ = User.objects.get_or_create(
            username='kushal',
            defaults={'email': 'kushal@ntc.net.np', 'is_active': True}
        )
        user1.set_password('password123')
        user1.save()

        user2, _ = User.objects.get_or_create(
            username='priya_sharma',
            defaults={'is_active': True}
        )
        user2.set_password('password123')
        user2.save()

        # Create memberships
        domain_ct = ContentType.objects.get_for_model(Domain)
        org_ct = ContentType.objects.get_for_model(Organization)
        dept_ct = ContentType.objects.get_for_model(Department)
        wing_ct = ContentType.objects.get_for_model(Wing)

        # Kushal - Admin in domain1
        Membership.objects.get_or_create(
            user=user1, content_type=domain_ct, object_id=domain1.id, role=admin_role
        )

        # Priya - User in Security Wing
        Membership.objects.get_or_create(
            user=user2, content_type=wing_ct, object_id=wing3.id, role=user_role
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded database with sample data'))