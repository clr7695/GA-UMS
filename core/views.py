from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Max, Min, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.decorators import role_required
from core.forms import EnrollmentForm, ProfessorForm, SectionForm
from core.models import Department, Enrollment, Funding, Paper, Professor, Section


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        error = "Invalid username or password."

    return render(request, "core/login.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    profile = getattr(request.user, "userprofile", None)
    role = profile.role if profile else None
    return render(request, "core/dashboard.html", {"role": role})


PROFESSOR_SORT_FIELDS = {
    "name": "name",
    "dept": "department__name",
    "salary": "salary",
}


@role_required("admin")
def professor_roster(request):
    sort = request.GET.get("sort", "name")
    sort_field = PROFESSOR_SORT_FIELDS.get(sort, "name")

    if request.method == "POST":
        form = ProfessorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(f"{reverse('roster')}?sort={sort}")
    else:
        form = ProfessorForm()

    professors = Professor.objects.select_related("department").order_by(sort_field)
    return render(
        request,
        "core/roster.html",
        {"professors": professors, "sort": sort, "form": form},
    )


@role_required("admin")
def salary_table(request):
    results = (
        Professor.objects.values("department__name")
        .annotate(min_sal=Min("salary"), max_sal=Max("salary"), avg_sal=Avg("salary"))
        .order_by("department__name")
    )
    return render(request, "core/salary.html", {"results": results})


@role_required("admin")
def professor_performance(request):
    professors = Professor.objects.order_by("name")

    professor_id = request.GET.get("professor_id") or ""
    year = request.GET.get("year") or ""
    semester = request.GET.get("semester") or ""

    professor = None
    stats = None
    if professor_id and year.isdigit() and semester:
        professor = get_object_or_404(Professor, pk=professor_id)
        sections = Section.objects.filter(professor=professor, year=int(year), semester=semester)
        student_count = (
            Enrollment.objects.filter(section__in=sections).values("student").distinct().count()
        )
        total_funding = Funding.objects.filter(professor=professor).aggregate(total=Sum("amount"))[
            "total"
        ] or 0
        paper_count = Paper.objects.filter(professor=professor).count()
        stats = {
            "section_count": sections.count(),
            "student_count": student_count,
            "total_funding": total_funding,
            "paper_count": paper_count,
        }

    return render(
        request,
        "core/performance.html",
        {
            "professors": professors,
            "professor": professor,
            "professor_id": professor_id,
            "year": year,
            "semester": semester,
            "stats": stats,
        },
    )


@role_required("professor")
def my_sections(request):
    professor = request.user.userprofile.professor
    if professor is None:
        return render(request, "core/my_sections.html", {"no_professor": True})

    if request.method == "POST":
        form = SectionForm(request.POST)
        if form.is_valid():
            section = form.save(commit=False)
            section.professor = professor
            section.save()
            return redirect("my_sections")
    else:
        form = SectionForm()

    semester = request.GET.get("semester") or ""
    year = request.GET.get("year") or ""

    sections = Section.objects.filter(professor=professor)
    if semester:
        sections = sections.filter(semester=semester)
    if year.isdigit():
        sections = sections.filter(year=int(year))

    sections = (
        sections.select_related("course")
        .annotate(student_count=Count("enrollment"))
        .order_by("year", "semester")
    )

    return render(
        request,
        "core/my_sections.html",
        {"sections": sections, "semester": semester, "year": year, "form": form},
    )


@role_required("professor")
def section_roster(request):
    professor = request.user.userprofile.professor
    if professor is None:
        return render(request, "core/section_roster.html", {"no_professor": True})

    my_own_sections = Section.objects.filter(professor=professor).select_related("course")

    chosen_section = None
    enrollments = None
    form = None
    section_id = request.GET.get("section_id") or request.POST.get("section_id")
    if section_id:
        chosen_section = get_object_or_404(Section, pk=section_id, professor=professor)
        already_enrolled_ids = Enrollment.objects.filter(section=chosen_section).values_list(
            "student_id", flat=True
        )

        if request.method == "POST":
            form = EnrollmentForm(request.POST, already_enrolled_ids=already_enrolled_ids)
            if form.is_valid():
                enrollment = form.save(commit=False)
                enrollment.section = chosen_section
                enrollment.save()
                return redirect(f"{reverse('section_roster')}?section_id={chosen_section.id}")
        else:
            form = EnrollmentForm(already_enrolled_ids=already_enrolled_ids)

        enrollments = Enrollment.objects.filter(section=chosen_section).select_related("student")

    return render(
        request,
        "core/section_roster.html",
        {
            "sections": my_own_sections,
            "chosen_section": chosen_section,
            "enrollments": enrollments,
            "form": form,
        },
    )


@role_required("student")
def course_search(request):
    department_id = request.GET.get("department") or ""
    semester = request.GET.get("semester") or ""
    year = request.GET.get("year") or ""

    sections = Section.objects.all()
    if department_id.isdigit():
        sections = sections.filter(course__department_id=int(department_id))
    if year.isdigit():
        sections = sections.filter(year=int(year))
    if semester:
        sections = sections.filter(semester=semester)

    sections = sections.select_related("course__department", "professor").order_by("course__title")

    return render(
        request,
        "core/course_search.html",
        {
            "departments": Department.objects.order_by("name"),
            "sections": sections,
            "department_id": department_id,
            "semester": semester,
            "year": year,
        },
    )
