# University Management System — User Manual

This manual explains how to use each feature of the system, organized by the
role that can access it. All features require logging in first.

## Logging In

1. Navigate to the site's home page (`/`).
2. Enter your **username** and **password** in the login form.
3. Click **Log in**.
4. On success, you're redirected to your **Dashboard**, which shows your role
   and links to the features available to you.
5. If your credentials are wrong, the page reloads with the message
   *"Invalid username or password."* and you stay logged out.
6. Click **Log out** in the top navigation bar at any time to end your session.

Sample accounts (created by `python manage.py seed_data`), all using the
password `password123`:

| Username | Role | Linked record |
|---|---|---|
| `admin_test` | Admin | — |
| `prof_test` | Professor | Alice Chen |
| `student_test` | Student | Evan Brooks |

---

## F1 — Professor Roster (Admin)

**Who can access it:** Admin only. Navigating here as a professor or student
returns a 403 Forbidden page.

**How to use it:**
1. From the Dashboard, click **Professor Roster** (or visit `/roster/`).
2. The page lists every professor with their name, department, and salary.
3. Click a column header — **Name**, **Department**, or **Salary** — to
   re-sort the table by that field (adds `?sort=name`, `?sort=dept`, or
   `?sort=salary` to the URL).

**Example output** (sorted by Salary, ascending):

| Name | Department | Salary |
|---|---|---|
| Carla Diaz | Mathematics | 79000.00 |
| Dan Osei | Biology | 82000.00 |
| Bob Nguyen | Computer Science | 88000.00 |
| Alice Chen | Computer Science | 95000.00 |

---

## F2 — Salary Table (Admin)

**Who can access it:** Admin only.

**How to use it:**
1. From the Dashboard, click **Salary Table** (or visit `/salary/`).
2. The page shows one row per department, with the minimum, maximum, and
   average professor salary in that department. No input is required — the
   table loads immediately.

**Example output:**

| Department | Min Salary | Max Salary | Avg Salary |
|---|---|---|---|
| Biology | 82000.00 | 82000.00 | 82000.00 |
| Computer Science | 88000.00 | 95000.00 | 91500.00 |
| Mathematics | 79000.00 | 79000.00 | 79000.00 |

---

## F4 — My Sections (Professor)

**Who can access it:** Professors only, and only for sections they
personally teach. A professor whose account isn't linked to a Professor
record sees a warning instead of a table.

**How to use it:**
1. From the Dashboard, click **My Sections** (or visit `/my-sections/`).
2. By default, all of your sections (across every semester/year) are listed.
3. To narrow the results, choose a **Semester** from the dropdown and/or
   type a **Year**, then click **Filter**.
4. Each row shows the course, semester, year, and how many students are
   currently enrolled in that section.

**Example output** (logged in as `prof_test` / Alice Chen, filtered to
Fall 2025):

| Course | Semester | Year | Enrolled Students |
|---|---|---|---|
| Intro to Programming | Fall | 2025 | 3 |
| Database Systems | Fall | 2025 | 2 |

---

## F5 — Section Roster (Professor)

**Who can access it:** Professors only. The dropdown only ever lists
sections you teach — attempting to view another professor's section by
editing the URL returns a 404 Not Found.

**How to use it:**
1. From the Dashboard, click **Section Roster** (or visit
   `/section-roster/`).
2. Choose one of your sections from the **dropdown**.
3. Click **View Roster**.
4. The page lists the name of every student enrolled in that section.

**Example output** (Intro to Programming, Fall 2025):

| Student |
|---|
| Evan Brooks |
| Fatima Rahman |
| Grace Kim |

---

## F6 — Course Search (Student)

**Who can access it:** Students only.

**How to use it:**
1. From the Dashboard, click **Course Search** (or visit
   `/course-search/`).
2. Optionally choose a **Department**, **Semester**, and/or type a **Year**
   to narrow your search. Leaving a field on its default ("All …") includes
   every value for that field.
3. Click **Search**.
4. Matching course sections are listed with their course title, department,
   professor, semester, and year.

**Example output** (no filters applied — every section in the system):

| Course | Department | Professor | Semester | Year |
|---|---|---|---|---|
| Calculus I | Mathematics | Carla Diaz | Fall | 2025 |
| Database Systems | Computer Science | Alice Chen | Fall | 2025 |
| Genetics | Biology | Dan Osei | Spring | 2026 |
| Intro to Programming | Computer Science | Alice Chen | Fall | 2025 |
