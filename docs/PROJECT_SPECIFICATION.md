# DB-backed Web Application: University Management System (UMS)

## Project Specification

*This is a transcription of the original assignment specification
(`UMS Directions Original.pdf`), kept in the repository so the requirements
and deliverables it describes stay traceable alongside the code, the
[Design Manual](../DESIGN_MANUAL.md), and the [User Manual](../USER_MANUAL.md).*

Teams will design and implement a web-based university management system.
The system will make use of the university database that you have been
working on since the beginning of this semester but with some extension as
part of this project. The system will utilize the Django web framework to
connect to MySQL and to hold together all components of the system: loading
data from the database, representing the data as Python objects, and
dynamically creating a web page for displaying the data. The user interface
will be built using Django templates.

Your system will provide functionalities/features to support three kinds of
users (admins, profs, and students), as follows:

- **Admin** can do the following:
  - **F1. Roster**: Create a list of professors. In addition, the admin must
    have the option to sort the list by one of the following criteria:
    - by name
    - by dept, or
    - by salary.
  - **F2. Salary**: Create a table of minimum/maximum/average salaries by
    dept.
  - **F3. Performance**: Given a professor's name, an academic year, and a
    semester, show the following for the professor:
    - the number of course sections taught during the semester,
    - the number of students taught,
    - the total dollar amount of funding the professor has secured, and
    - the total number of papers the professor has published.
- **Professors** can do the following:
  - **F4**. Create the list of course sections and the number of students
    enrolled in each section that the professor taught in a chosen semester.
  - **F5**. Create the list of students enrolled in a chosen course section
    and semester the professor taught.
- **Students** can do the following:
  - **F6**. Query the list of course sections offered by a chosen department
    in a chosen year and semester.

## Deliverables

0. **Team formation**: Appoint a team leader; the team lead must email the
   instructor names of all team members.
1. **Create a project GitHub repository** with the instructor invited. This
   will allow the instructor to review your source code: review Git &
   GitHub by watching a crash course on YouTube.
   1. Review of initial design and implementation for feedback in class.
2. **Draft user manual and design manual** for feedback.
   1. Second demo of design and implementation for feedback in class.
3. **Project showcase presentation**: in class.
   1. (5 minutes for each team, 1 minute for Q&A.)
   2. Overview of system goal and required functionality.
   3. Design process & challenges encountered.
   4. Status of each functionality supported with screenshots.
   5. What remains to be done and how well the team has worked.
4. **System source code as well as user manual & design manual**:
   1. The implementation of each feature F1 to F6 **except F3**.
   2. The user manual.
   3. Design manual (design overview, E-R diagram and database schemas, and
      description of security assurance process).

### Additions

- This is now an **individual assignment**. It is being done as a small
  work project, not as a class project.

## Requirements traceability

| Item | Status | Where |
|---|---|---|
| F1. Roster (sort by name/dept/salary) + create a professor | Implemented | `core/views.py:professor_roster`, `core/forms.py:ProfessorForm`, User Manual §F1 |
| F2. Salary table (min/max/avg by dept) | Implemented (read-only; "create a table" refers to the report itself) | `core/views.py:salary_table`, User Manual §F2 |
| F3. Performance (sections/students for a semester + career funding/papers) | Implemented (beyond the deliverable 4.a minimum of "F1 to F6 except F3") | `core/views.py:professor_performance`, User Manual §F3, Design Manual §1 |
| F4. Course sections + enrollment counts for a professor + create a section | Implemented | `core/views.py:my_sections`, `core/forms.py:SectionForm`, User Manual §F4 |
| F5. Student roster for a chosen section + enroll a student | Implemented | `core/views.py:section_roster`, `core/forms.py:EnrollmentForm`, User Manual §F5 |
| F6. Course search by dept/year/semester | Implemented (read-only; spec says "query", not "create") | `core/views.py:course_search`, User Manual §F6 |
| User manual | Delivered | `USER_MANUAL.md` |
| Design manual (overview, E-R diagram/schema, security) | Delivered | `DESIGN_MANUAL.md` §1–3 |
| Team formation / GitHub repo with instructor invited / showcase presentation | Not applicable to source repo | Process/administrative deliverables (see "Additions": now an individual assignment) |
