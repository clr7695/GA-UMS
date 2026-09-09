from django.urls import path

from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("roster/", views.professor_roster, name="roster"),
    path("salary/", views.salary_table, name="salary"),
    path("my-sections/", views.my_sections, name="my_sections"),
    path("section-roster/", views.section_roster, name="section_roster"),
    path("course-search/", views.course_search, name="course_search"),
]
