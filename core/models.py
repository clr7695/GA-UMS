from django.contrib.auth.models import User
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Professor(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Student(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Course(models.Model):
    title = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    semester = models.CharField(max_length=20)  # e.g. 'Fall', 'Spring'
    year = models.IntegerField()

    def __str__(self):
        return f"{self.course.title} - {self.semester} {self.year}"


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("student", "section")

    def __str__(self):
        return f"{self.student.name} -> {self.section}"


class Funding(models.Model):
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.professor.name}: {self.amount}"


class Paper(models.Model):
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    title = models.CharField(max_length=300)

    def __str__(self):
        return self.title


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('professor', 'Professor'),
        ('student', 'Student'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    professor = models.ForeignKey(Professor, null=True, blank=True, on_delete=models.SET_NULL)
    student = models.ForeignKey(Student, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.user.username} ({self.role})"
