from django.contrib import admin

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


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "salary")
    list_filter = ("department",)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "department")
    list_filter = ("department",)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("course", "professor", "semester", "year")
    list_filter = ("semester", "year")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "section")


@admin.register(Funding)
class FundingAdmin(admin.ModelAdmin):
    list_display = ("professor", "amount")


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ("professor", "title")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "professor", "student")
    list_filter = ("role",)
