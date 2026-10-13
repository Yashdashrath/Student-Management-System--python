"""
Student Management System (Python version)
SCPL Mini Project - Academic Year 2026-27

A console-based, menu-driven application that stores student records
in a CSV-formatted text file (students.txt).

Run with:   python main.py
Optional:   python main.py path/to/other_file.txt   (use a different data file)
"""

import csv
import math
import os
import sys

DATA_FILE = "students.txt"                    # default data file
CSV_HEADER = ["roll_no", "name", "branch", "cgpa"]


# ----------------------------------------------------------------------
# Validation helpers (used by both the menu and the unit tests)
# ----------------------------------------------------------------------
def parse_roll_number(text):
    """Convert text to a positive integer roll number or raise ValueError."""
    try:
        roll_no = int(str(text).strip())
    except ValueError:
        raise ValueError("Roll number must be a whole number (e.g. 32).")
    if roll_no <= 0:
        raise ValueError("Roll number must be greater than 0.")
    return roll_no


def parse_cgpa(text):
    """Convert text to a CGPA between 0 and 10 or raise ValueError."""
    try:
        cgpa = float(str(text).strip())
    except ValueError:
        raise ValueError("CGPA must be a number (e.g. 8.5).")
    if math.isnan(cgpa) or math.isinf(cgpa):
        raise ValueError("CGPA must be a normal number between 0 and 10.")
    if cgpa < 0 or cgpa > 10:
        raise ValueError("Invalid CGPA! CGPA must be between 0 and 10.")
    return cgpa


def clean_text(text, field_name):
    """Trim spaces and make sure a text field (name / branch) is not empty."""
    value = " ".join(str(text).split())       # also collapses repeated spaces
    if not value:
        raise ValueError(field_name + " cannot be empty.")
    return value


# ----------------------------------------------------------------------
# Student class  (same four fields as the C++ version)
# ----------------------------------------------------------------------
class Student:
    def __init__(self, roll_no, name, branch, cgpa):
        self.roll_no = roll_no
        self.name = name
        self.branch = branch
        self.cgpa = cgpa

    def to_row(self):
        """Return the record as a list, ready to be written as one CSV row."""
        return [self.roll_no, self.name, self.branch, "{:.2f}".format(self.cgpa)]


# ----------------------------------------------------------------------
# StudentManagementSystem class  (all the operations)
# ----------------------------------------------------------------------
class StudentManagementSystem:
    def __init__(self, filename=DATA_FILE):
        self.filename = filename
        self.students = []                    # list of Student objects
        self.load_warnings = []               # messages about skipped rows

    # ---------------- file handling ----------------
    def load_from_file(self):
        """Read all records from the file. A missing file means 'no records yet'."""
        self.students = []
        self.load_warnings = []
        seen_rolls = set()

        if not os.path.exists(self.filename):
            return True                       # first run: nothing to load

        try:
            with open(self.filename, "r", newline="", encoding="utf-8") as file:
                reader = csv.reader(file)
                for line_no, row in enumerate(reader, start=1):
                    if not row or all(cell.strip() == "" for cell in row):
                        continue              # ignore blank lines
                    if line_no == 1 and [c.strip().lower() for c in row] == CSV_HEADER:
                        continue              # skip the header row
                    try:
                        if len(row) != 4:
                            raise ValueError("expected 4 fields, found %d" % len(row))
                        roll_no = parse_roll_number(row[0])
                        name = clean_text(row[1], "Name")
                        branch = clean_text(row[2], "Branch")
                        cgpa = parse_cgpa(row[3])
                    except ValueError as error:
                        self.load_warnings.append(
                            "Line %d skipped (%s)." % (line_no, error))
                        continue
                    if roll_no in seen_rolls:
                        self.load_warnings.append(
                            "Line %d skipped (duplicate roll number %d)." % (line_no, roll_no))
                        continue
                    seen_rolls.add(roll_no)
                    self.students.append(Student(roll_no, name, branch, cgpa))
        except (OSError, UnicodeDecodeError, csv.Error) as error:
            self.load_warnings.append("Could not read '%s': %s" % (self.filename, error))
            return False
        return True

    def save_to_file(self):
        """
        Write all records to the file.
        The data is first written to a temporary file and then swapped in, so a
        crash in the middle of saving cannot destroy the existing data file.
        """
        temp_name = self.filename + ".tmp"
        try:
            with open(temp_name, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(CSV_HEADER)
                for student in self.students:
                    writer.writerow(student.to_row())
            os.replace(temp_name, self.filename)
            return True
        except OSError as error:
            print("Error saving file:", error)
            if os.path.exists(temp_name):
                try:
                    os.remove(temp_name)
                except OSError:
                    pass
            return False

    # ---------------- helper methods ----------------
    def find_student(self, roll_no):
        """Return the Student with this roll number, or None."""
        for student in self.students:
            if student.roll_no == roll_no:
                return student
        return None

    def roll_exists(self, roll_no):
        return self.find_student(roll_no) is not None

    # ---------------- core operations (return (success, message)) ----------------
    def add_student(self, roll_no, name, branch, cgpa):
        try:
            roll_no = parse_roll_number(roll_no)
            name = clean_text(name, "Name")
            branch = clean_text(branch, "Branch")
            cgpa = parse_cgpa(cgpa)
        except ValueError as error:
            return False, str(error)

        if self.roll_exists(roll_no):
            return False, "Student with this roll number already exists!"

        new_student = Student(roll_no, name, branch, cgpa)
        self.students.append(new_student)
        if not self.save_to_file():
            self.students.remove(new_student)          # undo: memory matches file
            return False, "Could not save the record. Student was not added."
        return True, "Student added successfully!"

    def update_student(self, roll_no, name=None, branch=None, cgpa=None):
        """
        Update fields of an existing student. Pass None to keep a field unchanged.
        Every new value is validated BEFORE anything is changed, so a bad input
        can never leave a record half-updated.
        """
        student = self.find_student(roll_no)
        if student is None:
            return False, "Student not found!"

        try:
            new_name = student.name if name is None else clean_text(name, "Name")
            new_branch = student.branch if branch is None else clean_text(branch, "Branch")
            new_cgpa = student.cgpa if cgpa is None else parse_cgpa(cgpa)
        except ValueError as error:
            return False, str(error) + " Record not changed."

        old_values = (student.name, student.branch, student.cgpa)
        student.name, student.branch, student.cgpa = new_name, new_branch, new_cgpa
        if not self.save_to_file():
            student.name, student.branch, student.cgpa = old_values   # undo
            return False, "Could not save the changes. Record not changed."
        return True, "Student updated successfully!"

    def delete_student(self, roll_no):
        student = self.find_student(roll_no)
        if student is None:
            return False, "Student not found!"
        position = self.students.index(student)
        self.students.remove(student)
        if not self.save_to_file():
            self.students.insert(position, student)        # undo
            return False, "Could not save the changes. Student was not deleted."
        return True, "Student deleted successfully!"

    def average_cgpa(self):
        """Return the average CGPA, or None when there are no students."""
        if not self.students:
            return None
        total = sum(student.cgpa for student in self.students)
        return total / len(self.students)

    # ---------------- text formatting for the console ----------------
    def format_table(self):
        """Return all records as an aligned table (column widths adapt to the data)."""
        headers = ["Roll No", "Name", "Branch", "CGPA"]
        rows = [[str(s.roll_no), s.name, s.branch, "{:.2f}".format(s.cgpa)]
                for s in self.students]
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(cell))
        widths = [w + 3 for w in widths]                    # spacing between columns

        def line(cells):
            return "".join(cell.ljust(widths[i]) for i, cell in enumerate(cells)).rstrip()

        output = [line(headers), "-" * sum(widths)]
        output.extend(line(row) for row in rows)
        return "\n".join(output)


# ----------------------------------------------------------------------
# Console interface (menu-driven)
# ----------------------------------------------------------------------
def read_roll_number(prompt):
    """Ask for a roll number; return int, or None if the input is invalid."""
    try:
        return parse_roll_number(input(prompt))
    except ValueError as error:
        print("Invalid input!", error)
        return None


def add_student_menu(system):
    print()
    roll_no = read_roll_number("Enter Roll Number: ")
    if roll_no is None:
        return
    if system.roll_exists(roll_no):                         # check early, like the C++ code
        print("Student with this roll number already exists!")
        return
    name = input("Enter Name: ")
    branch = input("Enter Branch: ")
    cgpa = input("Enter CGPA: ")
    print(system.add_student(roll_no, name, branch, cgpa)[1])


def display_students_menu(system):
    if not system.students:
        print("\nNo students found!")
        return
    print()
    print(system.format_table())
    print("\nTotal students:", len(system.students))


def search_student_menu(system):
    print()
    roll_no = read_roll_number("Enter Roll Number to search: ")
    if roll_no is None:
        return
    student = system.find_student(roll_no)
    if student is None:
        print("Student not found!")
        return
    print("\nStudent Found!")
    print("-" * 25)
    print("Roll Number :", student.roll_no)
    print("Name        :", student.name)
    print("Branch      :", student.branch)
    print("CGPA        : {:.2f}".format(student.cgpa))


def update_student_menu(system):
    print()
    roll_no = read_roll_number("Enter Roll Number to update: ")
    if roll_no is None:
        return
    student = system.find_student(roll_no)
    if student is None:
        print("Student not found!")
        return
    print("(Press Enter to keep the current value)")
    new_name = input("Enter New Name [%s]: " % student.name).strip()
    new_branch = input("Enter New Branch [%s]: " % student.branch).strip()
    new_cgpa = input("Enter New CGPA [{:.2f}]: ".format(student.cgpa)).strip()
    success, message = system.update_student(
        roll_no,
        name=new_name or None,
        branch=new_branch or None,
        cgpa=new_cgpa or None)
    print(message)


def delete_student_menu(system):
    print()
    roll_no = read_roll_number("Enter Roll Number to delete: ")
    if roll_no is None:
        return
    print(system.delete_student(roll_no)[1])


def average_cgpa_menu(system):
    average = system.average_cgpa()
    if average is None:
        print("\nNo student records available!")
    else:
        print("\nAverage CGPA: {:.2f}".format(average))


def show_menu():
    print()
    print("=====================================")
    print("      STUDENT MANAGEMENT SYSTEM")
    print("=====================================")
    print("1. Add Student")
    print("2. Display All Students")
    print("3. Search Student")
    print("4. Update Student")
    print("5. Delete Student")
    print("6. Calculate Average CGPA")
    print("7. Exit")
    print("=====================================")


def run_menu(system):
    """Main loop: load records, then keep showing the menu until the user exits."""
    system.load_from_file()
    for warning in system.load_warnings:
        print("Warning:", warning)

    actions = {
        "1": add_student_menu,
        "2": display_students_menu,
        "3": search_student_menu,
        "4": update_student_menu,
        "5": delete_student_menu,
        "6": average_cgpa_menu,
    }

    while True:
        show_menu()
        try:
            choice = input("Enter your choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nInput closed. Exiting.")
            break
        if choice == "7":
            print("\nThank you for using Student Management System!")
            break
        action = actions.get(choice)
        if action is None:
            print("\nInvalid choice! Please enter a number from 1 to 7.")
            continue
        try:
            action(system)
        except (EOFError, KeyboardInterrupt):
            print("\n\nInput closed. Exiting.")
            break


def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else DATA_FILE
    system = StudentManagementSystem(filename)
    run_menu(system)


if __name__ == "__main__":
    main()
