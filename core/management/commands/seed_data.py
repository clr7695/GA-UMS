from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from core.models import (
    Course,
    Department,
    Enrollment,
    Funding,
    Paper,
    Professor,
    Section,
    Student,
    UserProfile,
)


class Command(BaseCommand):
    help = "Populates the database with sample data for development and testing."

    def handle(self, *args, **options):
        cs = Department.objects.get_or_create(name="Computer Science")[0]
        math = Department.objects.get_or_create(name="Mathematics")[0]
        bio = Department.objects.get_or_create(name="Biology")[0]

        alice = Professor.objects.get_or_create(
            name="Alice Chen", department=cs, defaults={"salary": "95000.00"}
        )[0]
        bob = Professor.objects.get_or_create(
            name="Bob Nguyen", department=cs, defaults={"salary": "88000.00"}
        )[0]
        carla = Professor.objects.get_or_create(
            name="Carla Diaz", department=math, defaults={"salary": "79000.00"}
        )[0]
        dan = Professor.objects.get_or_create(
            name="Dan Osei", department=bio, defaults={"salary": "82000.00"}
        )[0]

        Funding.objects.get_or_create(professor=alice, amount="250000.00")
        Funding.objects.get_or_create(professor=alice, amount="50000.00")
        Funding.objects.get_or_create(professor=carla, amount="120000.00")

        Paper.objects.get_or_create(professor=alice, title="Scalable Query Planning for OLAP")
        Paper.objects.get_or_create(professor=bob, title="A Survey of Container Scheduling")
        Paper.objects.get_or_create(professor=dan, title="Gene Expression in Zebrafish")

        students = [
            Student.objects.get_or_create(name=n)[0]
            for n in [
                "Evan Brooks",
                "Fatima Rahman",
                "Grace Kim",
                "Hassan Ali",
                "Ivy Torres",
            ]
        ]

        intro_cs = Course.objects.get_or_create(title="Intro to Programming", department=cs)[0]
        db_course = Course.objects.get_or_create(title="Database Systems", department=cs)[0]
        calc = Course.objects.get_or_create(title="Calculus I", department=math)[0]
        genetics = Course.objects.get_or_create(title="Genetics", department=bio)[0]

        sec1 = Section.objects.get_or_create(
            course=intro_cs, professor=alice, semester="Fall", year=2025
        )[0]
        sec2 = Section.objects.get_or_create(
            course=db_course, professor=alice, semester="Fall", year=2025
        )[0]
        sec3 = Section.objects.get_or_create(
            course=calc, professor=carla, semester="Fall", year=2025
        )[0]
        sec4 = Section.objects.get_or_create(
            course=genetics, professor=dan, semester="Spring", year=2026
        )[0]

        enrollments = [
            (students[0], sec1),
            (students[1], sec1),
            (students[2], sec1),
            (students[1], sec2),
            (students[3], sec2),
            (students[0], sec3),
            (students[4], sec3),
            (students[2], sec4),
        ]
        for student, section in enrollments:
            Enrollment.objects.get_or_create(student=student, section=section)

        admin_user = User.objects.get_or_create(
            username="admin_test", defaults={"is_staff": True, "is_superuser": True}
        )[0]
        admin_user.set_password("password123")
        admin_user.save()
        UserProfile.objects.get_or_create(user=admin_user, defaults={"role": "admin"})

        prof_user = User.objects.get_or_create(username="prof_test")[0]
        prof_user.set_password("password123")
        prof_user.save()
        UserProfile.objects.get_or_create(
            user=prof_user, defaults={"role": "professor", "professor": alice}
        )

        student_user = User.objects.get_or_create(username="student_test")[0]
        student_user.set_password("password123")
        student_user.save()
        UserProfile.objects.get_or_create(
            user=student_user, defaults={"role": "student", "student": students[0]}
        )

        self.stdout.write(self.style.SUCCESS("Sample data loaded."))
