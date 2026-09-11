from django import forms

from core.models import Course, Department, Enrollment, Professor, Section

SEMESTER_CHOICES = [
    ("Fall", "Fall"),
    ("Spring", "Spring"),
    ("Summer", "Summer"),
    ("Winter", "Winter"),
]


class ProfessorForm(forms.ModelForm):
    class Meta:
        model = Professor
        fields = ["name", "department", "salary"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "department": forms.Select(attrs={"class": "form-select"}),
            "salary": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["department"].queryset = Department.objects.order_by("name")


class SectionForm(forms.ModelForm):
    semester = forms.ChoiceField(
        choices=SEMESTER_CHOICES, widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = Section
        fields = ["course", "semester", "year"]
        widgets = {
            "course": forms.Select(attrs={"class": "form-select"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["course"].queryset = Course.objects.order_by("title")


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ["student"]
        widgets = {"student": forms.Select(attrs={"class": "form-select"})}

    def __init__(self, *args, already_enrolled_ids=(), **kwargs):
        super().__init__(*args, **kwargs)
        queryset = self.fields["student"].queryset.order_by("name")
        if already_enrolled_ids:
            queryset = queryset.exclude(id__in=already_enrolled_ids)
        self.fields["student"].queryset = queryset
