from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Max, Min
from django.test import RequestFactory, TestCase
from django.urls import reverse

from core.decorators import role_required
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


class ModelBasicsTests(TestCase):
    def setUp(self):
        self.cs = Department.objects.create(name="Computer Science")
        self.math = Department.objects.create(name="Mathematics")
        self.alice = Professor.objects.create(name="Alice Chen", department=self.cs, salary="95000.00")
        self.bob = Professor.objects.create(name="Bob Nguyen", department=self.cs, salary="85000.00")
        self.carla = Professor.objects.create(name="Carla Diaz", department=self.math, salary="79000.00")

    def test_string_representations(self):
        self.assertEqual(str(self.cs), "Computer Science")
        self.assertEqual(str(self.alice), "Alice Chen")

    def test_professor_department_relationship(self):
        self.assertEqual(self.alice.department, self.cs)
        self.assertIn(self.alice, self.cs.professor_set.all())

    def test_funding_and_papers_link_to_professor(self):
        Funding.objects.create(professor=self.alice, amount="250000.00")
        Paper.objects.create(professor=self.alice, title="Scalable Query Planning")

        self.assertEqual(self.alice.funding_set.count(), 1)
        self.assertEqual(self.alice.paper_set.first().title, "Scalable Query Planning")


class CascadeDeleteTests(TestCase):
    def setUp(self):
        self.cs = Department.objects.create(name="Computer Science")
        self.alice = Professor.objects.create(name="Alice Chen", department=self.cs, salary="95000.00")
        self.course = Course.objects.create(title="Intro to Programming", department=self.cs)
        self.section = Section.objects.create(
            course=self.course, professor=self.alice, semester="Fall", year=2025
        )
        self.student = Student.objects.create(name="Evan Brooks")
        self.enrollment = Enrollment.objects.create(student=self.student, section=self.section)

    def test_deleting_professor_cascades_to_sections_and_enrollments(self):
        self.alice.delete()
        self.assertFalse(Section.objects.filter(pk=self.section.pk).exists())
        self.assertFalse(Enrollment.objects.filter(pk=self.enrollment.pk).exists())

    def test_deleting_student_cascades_to_enrollment_only(self):
        self.student.delete()
        self.assertFalse(Enrollment.objects.filter(pk=self.enrollment.pk).exists())
        self.assertTrue(Section.objects.filter(pk=self.section.pk).exists())


class UserProfileTests(TestCase):
    def setUp(self):
        self.cs = Department.objects.create(name="Computer Science")
        self.alice = Professor.objects.create(name="Alice Chen", department=self.cs, salary="95000.00")
        self.user = User.objects.create_user(username="prof_alice", password="testpass123")
        self.profile = UserProfile.objects.create(user=self.user, role="professor", professor=self.alice)

    def test_role_and_linked_professor(self):
        self.assertEqual(self.profile.role, "professor")
        self.assertEqual(self.profile.professor, self.alice)

    def test_deleting_professor_sets_profile_professor_to_null(self):
        self.alice.delete()
        self.profile.refresh_from_db()
        self.assertIsNone(self.profile.professor)
        # The user account itself and its profile should survive.
        self.assertTrue(UserProfile.objects.filter(pk=self.profile.pk).exists())


class QueryPatternTests(TestCase):
    """Exercises the ORM query patterns the doc specifies for F1, F2, F4, F5, F6."""

    def setUp(self):
        self.cs = Department.objects.create(name="Computer Science")
        self.math = Department.objects.create(name="Mathematics")

        self.alice = Professor.objects.create(name="Alice Chen", department=self.cs, salary="95000.00")
        self.bob = Professor.objects.create(name="Bob Nguyen", department=self.cs, salary="85000.00")
        self.carla = Professor.objects.create(name="Carla Diaz", department=self.math, salary="79000.00")

        self.intro_cs = Course.objects.create(title="Intro to Programming", department=self.cs)
        self.calc = Course.objects.create(title="Calculus I", department=self.math)

        self.sec_fall = Section.objects.create(
            course=self.intro_cs, professor=self.alice, semester="Fall", year=2025
        )
        self.sec_spring = Section.objects.create(
            course=self.intro_cs, professor=self.alice, semester="Spring", year=2026
        )
        self.sec_calc = Section.objects.create(
            course=self.calc, professor=self.carla, semester="Fall", year=2025
        )

        self.students = [Student.objects.create(name=n) for n in ["Evan", "Fatima", "Grace"]]
        Enrollment.objects.create(student=self.students[0], section=self.sec_fall)
        Enrollment.objects.create(student=self.students[1], section=self.sec_fall)
        Enrollment.objects.create(student=self.students[2], section=self.sec_calc)

    def test_f1_professor_roster_sortable(self):
        by_salary = list(Professor.objects.all().order_by("salary").values_list("name", flat=True))
        self.assertEqual(by_salary, ["Carla Diaz", "Bob Nguyen", "Alice Chen"])

        by_name = list(Professor.objects.all().order_by("name").values_list("name", flat=True))
        self.assertEqual(by_name, ["Alice Chen", "Bob Nguyen", "Carla Diaz"])

    def test_f2_salary_aggregation_by_department(self):
        results = {
            row["department__name"]: row
            for row in Professor.objects.values("department__name").annotate(
                min_sal=Min("salary"), max_sal=Max("salary"), avg_sal=Avg("salary")
            )
        }
        self.assertEqual(results["Computer Science"]["min_sal"], 85000)
        self.assertEqual(results["Computer Science"]["max_sal"], 95000)
        self.assertEqual(results["Mathematics"]["min_sal"], 79000)
        self.assertEqual(results["Mathematics"]["max_sal"], 79000)

    def test_f4_my_sections_with_enrollment_count(self):
        sections = Section.objects.filter(professor=self.alice, semester="Fall", year=2025).annotate(
            student_count=Count("enrollment")
        )
        self.assertEqual(sections.count(), 1)
        self.assertEqual(sections.first().student_count, 2)

        # A different semester for the same professor should return nothing enrolled.
        spring_sections = Section.objects.filter(
            professor=self.alice, semester="Spring", year=2026
        ).annotate(student_count=Count("enrollment"))
        self.assertEqual(spring_sections.first().student_count, 0)

    def test_f5_section_roster_lists_enrolled_students(self):
        enrollments = Enrollment.objects.filter(section=self.sec_fall).select_related("student")
        names = sorted(e.student.name for e in enrollments)
        self.assertEqual(names, ["Evan", "Fatima"])

    def test_f6_course_search_by_department_year_semester(self):
        sections = Section.objects.filter(
            course__department=self.cs, year=2025, semester="Fall"
        ).select_related("course", "professor")
        self.assertEqual(sections.count(), 1)
        self.assertEqual(sections.first().professor, self.alice)

        # A search for a semester with no matching sections returns empty.
        no_match = Section.objects.filter(course__department=self.math, year=2026, semester="Spring")
        self.assertEqual(no_match.count(), 0)


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="testpass123")
        UserProfile.objects.create(user=self.user, role="admin")

    def test_login_success_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("login"), {"username": "alice", "password": "testpass123"}
        )
        self.assertRedirects(response, reverse("dashboard"))

    def test_login_invalid_credentials_shows_error(self):
        response = self.client.post(
            reverse("login"), {"username": "alice", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password.")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_dashboard_shows_role_once_logged_in(self):
        self.client.login(username="alice", password="testpass123")
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "admin")

    def test_logout_clears_session(self):
        self.client.login(username="alice", password="testpass123")
        self.client.get(reverse("logout"))
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")


class RoleRequiredDecoratorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_user(username="admin1", password="x")
        UserProfile.objects.create(user=self.admin_user, role="admin")
        self.student_user = User.objects.create_user(username="student1", password="x")
        UserProfile.objects.create(user=self.student_user, role="student")
        self.no_profile_user = User.objects.create_user(username="noprofile", password="x")

        @role_required("admin")
        def admin_only_view(request):
            return "ok"

        self.admin_only_view = admin_only_view

    def test_allows_matching_role(self):
        request = self.factory.get("/fake-admin-page/")
        request.user = self.admin_user
        self.assertEqual(self.admin_only_view(request), "ok")

    def test_denies_wrong_role(self):
        request = self.factory.get("/fake-admin-page/")
        request.user = self.student_user
        with self.assertRaises(PermissionDenied):
            self.admin_only_view(request)

    def test_denies_user_with_no_profile(self):
        request = self.factory.get("/fake-admin-page/")
        request.user = self.no_profile_user
        with self.assertRaises(PermissionDenied):
            self.admin_only_view(request)


class ProfessorRosterViewTests(TestCase):
    def setUp(self):
        self.cs = Department.objects.create(name="Computer Science")
        self.math = Department.objects.create(name="Mathematics")
        Professor.objects.create(name="Zoe Adams", department=self.math, salary="70000.00")
        Professor.objects.create(name="Alan Brooks", department=self.cs, salary="90000.00")

        self.admin_user = User.objects.create_user(username="admin1", password="testpass123")
        UserProfile.objects.create(user=self.admin_user, role="admin")
        self.student_user = User.objects.create_user(username="student1", password="testpass123")
        UserProfile.objects.create(user=self.student_user, role="student")

    def test_requires_login(self):
        response = self.client.get(reverse("roster"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('roster')}")

    def test_denies_non_admin_role(self):
        self.client.login(username="student1", password="testpass123")
        response = self.client.get(reverse("roster"))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_view_roster(self):
        self.client.login(username="admin1", password="testpass123")
        response = self.client.get(reverse("roster"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Zoe Adams")
        self.assertContains(response, "Alan Brooks")

    def test_admin_can_create_professor(self):
        self.client.login(username="admin1", password="testpass123")
        response = self.client.post(
            reverse("roster"),
            {"name": "New Prof", "department": self.cs.id, "salary": "72000.00"},
        )
        self.assertRedirects(response, f"{reverse('roster')}?sort=name")
        self.assertTrue(Professor.objects.filter(name="New Prof", department=self.cs).exists())

    def test_create_professor_rejects_invalid_data(self):
        self.client.login(username="admin1", password="testpass123")
        response = self.client.post(
            reverse("roster"),
            {"name": "", "department": self.cs.id, "salary": "72000.00"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Professor.objects.filter(name="").exists())

    def test_denies_non_admin_creating_professor(self):
        self.client.login(username="student1", password="testpass123")
        response = self.client.post(
            reverse("roster"),
            {"name": "New Prof", "department": self.cs.id, "salary": "72000.00"},
        )
        self.assertEqual(response.status_code, 403)

    def test_sort_by_name(self):
        self.client.login(username="admin1", password="testpass123")
        response = self.client.get(reverse("roster"), {"sort": "name"})
        names = [p.name for p in response.context["professors"]]
        self.assertEqual(names, ["Alan Brooks", "Zoe Adams"])

    def test_sort_by_salary(self):
        self.client.login(username="admin1", password="testpass123")
        response = self.client.get(reverse("roster"), {"sort": "salary"})
        names = [p.name for p in response.context["professors"]]
        self.assertEqual(names, ["Zoe Adams", "Alan Brooks"])

    def test_sort_by_dept(self):
        self.client.login(username="admin1", password="testpass123")
        response = self.client.get(reverse("roster"), {"sort": "dept"})
        names = [p.name for p in response.context["professors"]]
        self.assertEqual(names, ["Alan Brooks", "Zoe Adams"])

    def test_unknown_sort_falls_back_to_name(self):
        self.client.login(username="admin1", password="testpass123")
        response = self.client.get(reverse("roster"), {"sort": "not_a_real_field"})
        self.assertEqual(response.status_code, 200)
        names = [p.name for p in response.context["professors"]]
        self.assertEqual(names, ["Alan Brooks", "Zoe Adams"])


class SalaryTableViewTests(TestCase):
    def setUp(self):
        self.cs = Department.objects.create(name="Computer Science")
        self.math = Department.objects.create(name="Mathematics")
        Professor.objects.create(name="Alice Chen", department=self.cs, salary="95000.00")
        Professor.objects.create(name="Bob Nguyen", department=self.cs, salary="85000.00")
        Professor.objects.create(name="Carla Diaz", department=self.math, salary="79000.00")

        self.admin_user = User.objects.create_user(username="admin1", password="testpass123")
        UserProfile.objects.create(user=self.admin_user, role="admin")
        self.student_user = User.objects.create_user(username="student1", password="testpass123")
        UserProfile.objects.create(user=self.student_user, role="student")

    def test_requires_login(self):
        response = self.client.get(reverse("salary"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('salary')}")

    def test_denies_non_admin_role(self):
        self.client.login(username="student1", password="testpass123")
        response = self.client.get(reverse("salary"))
        self.assertEqual(response.status_code, 403)

    def test_aggregation_values_grouped_by_department(self):
        self.client.login(username="admin1", password="testpass123")
        response = self.client.get(reverse("salary"))
        self.assertEqual(response.status_code, 200)
        results = {row["department__name"]: row for row in response.context["results"]}

        self.assertEqual(results["Computer Science"]["min_sal"], 85000)
        self.assertEqual(results["Computer Science"]["max_sal"], 95000)
        self.assertEqual(results["Computer Science"]["avg_sal"], 90000)
        self.assertEqual(results["Mathematics"]["min_sal"], 79000)
        self.assertEqual(results["Mathematics"]["max_sal"], 79000)
        self.assertEqual(results["Mathematics"]["avg_sal"], 79000)

    def test_page_renders_department_rows(self):
        self.client.login(username="admin1", password="testpass123")
        response = self.client.get(reverse("salary"))
        self.assertContains(response, "Computer Science")
        self.assertContains(response, "Mathematics")


class ProfessorPerformanceViewTests(TestCase):
    def setUp(self):
        self.cs = Department.objects.create(name="Computer Science")
        self.alice = Professor.objects.create(name="Alice Chen", department=self.cs, salary="95000.00")
        self.bob = Professor.objects.create(name="Bob Nguyen", department=self.cs, salary="85000.00")
        self.intro_cs = Course.objects.create(title="Intro to Programming", department=self.cs)
        self.db_course = Course.objects.create(title="Database Systems", department=self.cs)

        self.sec_fall_intro = Section.objects.create(
            course=self.intro_cs, professor=self.alice, semester="Fall", year=2025
        )
        self.sec_fall_db = Section.objects.create(
            course=self.db_course, professor=self.alice, semester="Fall", year=2025
        )
        self.sec_spring = Section.objects.create(
            course=self.intro_cs, professor=self.alice, semester="Spring", year=2026
        )

        self.students = [Student.objects.create(name=n) for n in ["Evan", "Fatima", "Grace"]]
        # Evan is in both of Alice's Fall sections and should only count once.
        Enrollment.objects.create(student=self.students[0], section=self.sec_fall_intro)
        Enrollment.objects.create(student=self.students[0], section=self.sec_fall_db)
        Enrollment.objects.create(student=self.students[1], section=self.sec_fall_db)

        Funding.objects.create(professor=self.alice, amount="100000.00")
        Funding.objects.create(professor=self.alice, amount="50000.00")
        Paper.objects.create(professor=self.alice, title="Paper One")
        Paper.objects.create(professor=self.alice, title="Paper Two")

        self.admin_user = User.objects.create_user(username="admin1", password="testpass123")
        UserProfile.objects.create(user=self.admin_user, role="admin")
        self.student_user = User.objects.create_user(username="student1", password="testpass123")
        UserProfile.objects.create(user=self.student_user, role="student")

    def test_requires_login(self):
        response = self.client.get(reverse("performance"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('performance')}")

    def test_denies_non_admin_role(self):
        self.client.login(username="student1", password="testpass123")
        response = self.client.get(reverse("performance"))
        self.assertEqual(response.status_code, 403)

    def test_no_selection_shows_no_stats(self):
        self.client.login(username="admin1", password="testpass123")
        response = self.client.get(reverse("performance"))
        self.assertIsNone(response.context["stats"])

    def test_performance_stats_for_chosen_semester(self):
        self.client.login(username="admin1", password="testpass123")
        response = self.client.get(
            reverse("performance"),
            {"professor_id": self.alice.id, "year": "2025", "semester": "Fall"},
        )
        stats = response.context["stats"]
        self.assertEqual(stats["section_count"], 2)
        self.assertEqual(stats["student_count"], 2)
        self.assertEqual(stats["total_funding"], 150000)
        self.assertEqual(stats["paper_count"], 2)

    def test_semester_with_no_sections_still_shows_career_totals(self):
        self.client.login(username="admin1", password="testpass123")
        response = self.client.get(
            reverse("performance"),
            {"professor_id": self.bob.id, "year": "2025", "semester": "Fall"},
        )
        stats = response.context["stats"]
        self.assertEqual(stats["section_count"], 0)
        self.assertEqual(stats["student_count"], 0)
        self.assertEqual(stats["total_funding"], 0)
        self.assertEqual(stats["paper_count"], 0)


class MySectionsViewTests(TestCase):
    def setUp(self):
        self.cs = Department.objects.create(name="Computer Science")
        self.alice = Professor.objects.create(name="Alice Chen", department=self.cs, salary="95000.00")
        self.bob = Professor.objects.create(name="Bob Nguyen", department=self.cs, salary="85000.00")
        self.intro_cs = Course.objects.create(title="Intro to Programming", department=self.cs)

        self.sec_fall = Section.objects.create(
            course=self.intro_cs, professor=self.alice, semester="Fall", year=2025
        )
        self.sec_spring = Section.objects.create(
            course=self.intro_cs, professor=self.alice, semester="Spring", year=2026
        )
        self.bobs_section = Section.objects.create(
            course=self.intro_cs, professor=self.bob, semester="Fall", year=2025
        )

        self.students = [Student.objects.create(name=n) for n in ["Evan", "Fatima"]]
        Enrollment.objects.create(student=self.students[0], section=self.sec_fall)
        Enrollment.objects.create(student=self.students[1], section=self.sec_fall)

        self.prof_user = User.objects.create_user(username="prof_alice", password="testpass123")
        UserProfile.objects.create(user=self.prof_user, role="professor", professor=self.alice)

        self.student_user = User.objects.create_user(username="student1", password="testpass123")
        UserProfile.objects.create(user=self.student_user, role="student")

        self.no_link_user = User.objects.create_user(username="prof_nolink", password="testpass123")
        UserProfile.objects.create(user=self.no_link_user, role="professor")

    def test_requires_login(self):
        response = self.client.get(reverse("my_sections"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('my_sections')}")

    def test_denies_non_professor_role(self):
        self.client.login(username="student1", password="testpass123")
        response = self.client.get(reverse("my_sections"))
        self.assertEqual(response.status_code, 403)

    def test_shows_only_own_sections_with_counts(self):
        self.client.login(username="prof_alice", password="testpass123")
        response = self.client.get(reverse("my_sections"))
        sections = list(response.context["sections"])
        self.assertEqual(len(sections), 2)
        self.assertNotIn(self.bobs_section, sections)
        fall_section = next(s for s in sections if s.semester == "Fall")
        self.assertEqual(fall_section.student_count, 2)

    def test_filters_by_semester_and_year(self):
        self.client.login(username="prof_alice", password="testpass123")
        response = self.client.get(reverse("my_sections"), {"semester": "Spring", "year": "2026"})
        sections = list(response.context["sections"])
        self.assertEqual(sections, [self.sec_spring])

    def test_professor_with_no_linked_record_sees_warning(self):
        self.client.login(username="prof_nolink", password="testpass123")
        response = self.client.get(reverse("my_sections"))
        self.assertTrue(response.context["no_professor"])

    def test_professor_can_create_own_section(self):
        self.client.login(username="prof_alice", password="testpass123")
        response = self.client.post(
            reverse("my_sections"),
            {"course": self.intro_cs.id, "semester": "Summer", "year": "2026"},
        )
        self.assertRedirects(response, reverse("my_sections"))
        section = Section.objects.get(professor=self.alice, semester="Summer", year=2026)
        self.assertEqual(section.course, self.intro_cs)

    def test_create_section_rejects_invalid_semester(self):
        self.client.login(username="prof_alice", password="testpass123")
        response = self.client.post(
            reverse("my_sections"),
            {"course": self.intro_cs.id, "semester": "NotASemester", "year": "2026"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Section.objects.filter(professor=self.alice, semester="NotASemester").exists())


class SectionRosterViewTests(TestCase):
    def setUp(self):
        self.cs = Department.objects.create(name="Computer Science")
        self.alice = Professor.objects.create(name="Alice Chen", department=self.cs, salary="95000.00")
        self.bob = Professor.objects.create(name="Bob Nguyen", department=self.cs, salary="85000.00")
        self.intro_cs = Course.objects.create(title="Intro to Programming", department=self.cs)

        self.sec_alice = Section.objects.create(
            course=self.intro_cs, professor=self.alice, semester="Fall", year=2025
        )
        self.sec_bob = Section.objects.create(
            course=self.intro_cs, professor=self.bob, semester="Fall", year=2025
        )

        self.students = [Student.objects.create(name=n) for n in ["Evan", "Fatima"]]
        Enrollment.objects.create(student=self.students[0], section=self.sec_alice)
        Enrollment.objects.create(student=self.students[1], section=self.sec_alice)

        self.prof_user = User.objects.create_user(username="prof_alice", password="testpass123")
        UserProfile.objects.create(user=self.prof_user, role="professor", professor=self.alice)

    def test_requires_login(self):
        response = self.client.get(reverse("section_roster"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('section_roster')}")

    def test_lists_enrolled_students_for_own_section(self):
        self.client.login(username="prof_alice", password="testpass123")
        response = self.client.get(reverse("section_roster"), {"section_id": self.sec_alice.id})
        names = sorted(e.student.name for e in response.context["enrollments"])
        self.assertEqual(names, ["Evan", "Fatima"])

    def test_cannot_view_another_professors_section(self):
        self.client.login(username="prof_alice", password="testpass123")
        response = self.client.get(reverse("section_roster"), {"section_id": self.sec_bob.id})
        self.assertEqual(response.status_code, 404)

    def test_no_section_chosen_shows_dropdown_only(self):
        self.client.login(username="prof_alice", password="testpass123")
        response = self.client.get(reverse("section_roster"))
        self.assertIsNone(response.context["chosen_section"])

    def test_professor_can_enroll_student_in_own_section(self):
        new_student = Student.objects.create(name="Grace Kim")
        self.client.login(username="prof_alice", password="testpass123")
        response = self.client.post(
            reverse("section_roster"),
            {"section_id": self.sec_alice.id, "student": new_student.id},
        )
        self.assertRedirects(response, f"{reverse('section_roster')}?section_id={self.sec_alice.id}")
        self.assertTrue(
            Enrollment.objects.filter(section=self.sec_alice, student=new_student).exists()
        )

    def test_cannot_enroll_already_enrolled_student_twice(self):
        self.client.login(username="prof_alice", password="testpass123")
        response = self.client.post(
            reverse("section_roster"),
            {"section_id": self.sec_alice.id, "student": self.students[0].id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Enrollment.objects.filter(section=self.sec_alice, student=self.students[0]).count(), 1
        )

    def test_cannot_enroll_student_into_another_professors_section(self):
        new_student = Student.objects.create(name="Grace Kim")
        self.client.login(username="prof_alice", password="testpass123")
        response = self.client.post(
            reverse("section_roster"),
            {"section_id": self.sec_bob.id, "student": new_student.id},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Enrollment.objects.filter(section=self.sec_bob, student=new_student).exists())


class CourseSearchViewTests(TestCase):
    def setUp(self):
        self.cs = Department.objects.create(name="Computer Science")
        self.math = Department.objects.create(name="Mathematics")
        self.alice = Professor.objects.create(name="Alice Chen", department=self.cs, salary="95000.00")
        self.carla = Professor.objects.create(name="Carla Diaz", department=self.math, salary="79000.00")

        self.intro_cs = Course.objects.create(title="Intro to Programming", department=self.cs)
        self.calc = Course.objects.create(title="Calculus I", department=self.math)

        self.sec_cs_fall = Section.objects.create(
            course=self.intro_cs, professor=self.alice, semester="Fall", year=2025
        )
        self.sec_cs_spring = Section.objects.create(
            course=self.intro_cs, professor=self.alice, semester="Spring", year=2026
        )
        self.sec_math_fall = Section.objects.create(
            course=self.calc, professor=self.carla, semester="Fall", year=2025
        )

        self.student_user = User.objects.create_user(username="student1", password="testpass123")
        UserProfile.objects.create(user=self.student_user, role="student")

        self.admin_user = User.objects.create_user(username="admin1", password="testpass123")
        UserProfile.objects.create(user=self.admin_user, role="admin")

    def test_requires_login(self):
        response = self.client.get(reverse("course_search"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('course_search')}")

    def test_denies_non_student_role(self):
        self.client.login(username="admin1", password="testpass123")
        response = self.client.get(reverse("course_search"))
        self.assertEqual(response.status_code, 403)

    def test_no_filters_returns_all_sections(self):
        self.client.login(username="student1", password="testpass123")
        response = self.client.get(reverse("course_search"))
        self.assertEqual(response.context["sections"].count(), 3)

    def test_filters_by_department_year_semester(self):
        self.client.login(username="student1", password="testpass123")
        response = self.client.get(
            reverse("course_search"),
            {"department": self.cs.id, "year": "2025", "semester": "Fall"},
        )
        sections = list(response.context["sections"])
        self.assertEqual(sections, [self.sec_cs_fall])

    def test_filter_with_no_matches_returns_empty(self):
        self.client.login(username="student1", password="testpass123")
        response = self.client.get(
            reverse("course_search"),
            {"department": self.math.id, "year": "2026", "semester": "Spring"},
        )
        self.assertEqual(response.context["sections"].count(), 0)

    def test_page_render_does_not_n_plus_one_on_department(self):
        # Rendering department/professor names for N sections should take a
        # fixed number of queries, not one extra query per row.
        self.client.login(username="student1", password="testpass123")
        with self.assertNumQueries(5):
            response = self.client.get(reverse("course_search"))
            str(response.content)
