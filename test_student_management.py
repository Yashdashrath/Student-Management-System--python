"""
Unit tests for the Student Management System.
Every test uses a temporary folder, so the real students.txt is never touched.

Run with:  python -m unittest -v test_student_management.py
"""

import builtins
import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

import main
from main import StudentManagementSystem


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.temp_dir.name, "students_test.txt")
        self.system = StudentManagementSystem(self.path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_three(self):
        self.system.add_student(1, "Sample Student One", "CSE", 8.5)
        self.system.add_student(2, "Sample Student Two", "IT", 7.25)
        self.system.add_student(3, "Sample Student Three", "ENTC", 9.1)


class TestAddStudent(BaseTest):
    def test_add_student(self):
        ok, msg = self.system.add_student(32, "Test User", "CSE", 8.0)
        self.assertTrue(ok)
        self.assertEqual(msg, "Student added successfully!")
        self.assertEqual(len(self.system.students), 1)

    def test_reject_duplicate_roll(self):
        self.system.add_student(5, "First", "CSE", 8.0)
        ok, msg = self.system.add_student(5, "Second", "IT", 7.0)
        self.assertFalse(ok)
        self.assertIn("already exists", msg)
        self.assertEqual(len(self.system.students), 1)

    def test_name_with_spaces(self):
        self.system.add_student(7, "Anil Kumar Rao", "ENTC", 6.5)
        self.assertEqual(self.system.find_student(7).name, "Anil Kumar Rao")

    def test_invalid_roll_number(self):
        for bad in ["abc", "", "3.5", "-4", "0"]:
            ok, _ = self.system.add_student(bad, "X", "CSE", 8)
            self.assertFalse(ok, "roll %r should be rejected" % bad)
        self.assertEqual(len(self.system.students), 0)

    def test_reject_invalid_cgpa_on_add(self):
        for bad in [-1, 10.5, "abc", "nan", "inf", ""]:
            ok, _ = self.system.add_student(1, "X", "CSE", bad)
            self.assertFalse(ok, "CGPA %r should be rejected" % bad)
        self.assertEqual(len(self.system.students), 0)

    def test_cgpa_boundaries_accepted(self):
        self.assertTrue(self.system.add_student(1, "Low", "CSE", 0)[0])
        self.assertTrue(self.system.add_student(2, "High", "CSE", 10)[0])

    def test_empty_name_rejected(self):
        self.assertFalse(self.system.add_student(1, "   ", "CSE", 8)[0])


class TestSearch(BaseTest):
    def test_search_existing(self):
        self.add_three()
        student = self.system.find_student(2)
        self.assertIsNotNone(student)
        self.assertEqual(student.name, "Sample Student Two")

    def test_search_missing(self):
        self.add_three()
        self.assertIsNone(self.system.find_student(99))


class TestUpdate(BaseTest):
    def test_update_details(self):
        self.add_three()
        ok, msg = self.system.update_student(1, name="New Name", branch="AI&DS", cgpa="9.0")
        self.assertTrue(ok)
        student = self.system.find_student(1)
        self.assertEqual((student.name, student.branch, student.cgpa),
                         ("New Name", "AI&DS", 9.0))

    def test_update_keeps_unchanged_fields(self):
        self.add_three()
        self.system.update_student(1, cgpa=9.5)
        student = self.system.find_student(1)
        self.assertEqual(student.name, "Sample Student One")
        self.assertEqual(student.branch, "CSE")

    def test_invalid_cgpa_does_not_change_record(self):
        self.add_three()
        ok, msg = self.system.update_student(1, name="Changed", branch="Changed", cgpa=15)
        self.assertFalse(ok)
        student = self.system.find_student(1)
        # nothing may be partly modified
        self.assertEqual((student.name, student.branch, student.cgpa),
                         ("Sample Student One", "CSE", 8.5))

    def test_invalid_cgpa_does_not_change_file(self):
        self.add_three()
        with open(self.path, encoding="utf-8") as f:
            before = f.read()
        self.system.update_student(1, cgpa=-3)
        with open(self.path, encoding="utf-8") as f:
            self.assertEqual(f.read(), before)

    def test_update_missing_student(self):
        ok, msg = self.system.update_student(42, name="Nobody")
        self.assertFalse(ok)
        self.assertEqual(msg, "Student not found!")


class TestDelete(BaseTest):
    def test_delete_student(self):
        self.add_three()
        ok, msg = self.system.delete_student(2)
        self.assertTrue(ok)
        self.assertIsNone(self.system.find_student(2))
        self.assertEqual([s.roll_no for s in self.system.students], [1, 3])

    def test_delete_missing_student(self):
        self.add_three()
        ok, msg = self.system.delete_student(99)
        self.assertFalse(ok)
        self.assertEqual(len(self.system.students), 3)


class TestAverage(BaseTest):
    def test_average_cgpa(self):
        self.add_three()                      # 8.5 + 7.25 + 9.1 = 24.85
        self.assertAlmostEqual(self.system.average_cgpa(), 24.85 / 3)
        self.assertEqual("{:.2f}".format(self.system.average_cgpa()), "8.28")

    def test_average_empty_list(self):
        self.assertIsNone(self.system.average_cgpa())    # no ZeroDivisionError


class TestFileHandling(BaseTest):
    def test_save_and_reload(self):
        self.add_three()
        self.system.update_student(3, cgpa=9.25)
        self.system.delete_student(2)
        reloaded = StudentManagementSystem(self.path)
        self.assertTrue(reloaded.load_from_file())
        self.assertEqual([(s.roll_no, s.name, s.branch, s.cgpa) for s in reloaded.students],
                         [(1, "Sample Student One", "CSE", 8.5),
                          (3, "Sample Student Three", "ENTC", 9.25)])

    def test_name_with_spaces_and_comma_survive_reload(self):
        self.system.add_student(9, "Rao, Anil Kumar", "Computer Science", 7.0)
        reloaded = StudentManagementSystem(self.path)
        reloaded.load_from_file()
        self.assertEqual(reloaded.find_student(9).name, "Rao, Anil Kumar")
        self.assertEqual(reloaded.find_student(9).branch, "Computer Science")

    def test_missing_file_is_ok(self):
        self.assertFalse(os.path.exists(self.path))
        self.assertTrue(self.system.load_from_file())
        self.assertEqual(self.system.students, [])

    def test_malformed_and_duplicate_rows_are_skipped(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("roll_no,name,branch,cgpa\n")
            f.write("1,Good One,CSE,8.00\n")
            f.write("abc,Bad Roll,CSE,8.00\n")        # bad roll
            f.write("2,Bad Cgpa,CSE,11\n")            # CGPA out of range
            f.write("3,Too Few Fields\n")             # wrong field count
            f.write("1,Duplicate Roll,IT,7.00\n")     # duplicate roll
            f.write("\n")                             # blank line
            f.write("4,Good Two,IT,9.00\n")
        self.system.load_from_file()
        self.assertEqual([s.roll_no for s in self.system.students], [1, 4])
        self.assertEqual(len(self.system.load_warnings), 4)

    def test_empty_file_is_ok(self):
        open(self.path, "w").close()
        self.assertTrue(self.system.load_from_file())
        self.assertEqual(self.system.students, [])

    def test_save_failure_rolls_back(self):
        bad_path = os.path.join(self.temp_dir.name, "no_such_folder", "x.txt")
        system = StudentManagementSystem(bad_path)
        with contextlib.redirect_stdout(io.StringIO()):
            ok, msg = system.add_student(1, "A", "CSE", 8)
        self.assertFalse(ok)
        self.assertEqual(system.students, [])

    def test_table_format_has_all_columns(self):
        self.add_three()
        table = self.system.format_table()
        for text in ["Roll No", "Name", "Branch", "CGPA", "Sample Student Three", "9.10"]:
            self.assertIn(text, table)


class TestMenu(BaseTest):
    """Drive the real menu with scripted keyboard input."""

    def run_session(self, inputs):
        answers = iter(inputs)
        out = io.StringIO()
        with mock.patch.object(builtins, "input", lambda prompt="": next(answers)):
            with contextlib.redirect_stdout(out):
                main.run_menu(StudentManagementSystem(self.path))
        return out.getvalue()

    def test_invalid_menu_choices_do_not_crash(self):
        text = self.run_session(["abc", "", "99", "-1", "7"])
        self.assertEqual(text.count("Invalid choice!"), 4)
        self.assertIn("Thank you for using", text)

    def test_exit_message(self):
        self.assertIn("Thank you for using", self.run_session(["7"]))

    def test_end_of_input_exits_cleanly(self):
        def raise_eof(prompt=""):
            raise EOFError
        out = io.StringIO()
        with mock.patch.object(builtins, "input", raise_eof):
            with contextlib.redirect_stdout(out):
                main.run_menu(StudentManagementSystem(self.path))
        self.assertIn("Exiting", out.getvalue())

    def test_records_persist_between_sessions(self):
        self.run_session(["1", "32", "Yash Dashrath", "CSE", "8.5", "7"])
        text = self.run_session(["2", "7"])   # a fresh program start
        self.assertIn("Yash Dashrath", text)
        self.assertIn("8.50", text)

    def test_full_workflow_through_menu(self):
        text = self.run_session([
            "1", "1", "Sample Student One", "CSE", "8.5",
            "1", "1",                                   # duplicate roll -> rejected at once
            "1", "2", "Sample Student Two", "IT", "7.5",
            "3", "2",                                   # search found
            "3", "50",                                  # search missing
            "4", "2", "", "", "12",                     # update, invalid CGPA
            "4", "2", "Renamed Two", "", "9",           # update, valid
            "6",                                        # average (8.5 + 9) / 2
            "5", "1",                                   # delete existing
            "5", "1",                                   # delete again -> not found
            "6",
            "7"])
        self.assertIn("Student added successfully!", text)
        self.assertIn("Student with this roll number already exists!", text)
        self.assertIn("Student Found!", text)
        self.assertIn("Student not found!", text)
        self.assertIn("Invalid CGPA! CGPA must be between 0 and 10. Record not changed.", text)
        self.assertIn("Student updated successfully!", text)
        self.assertIn("Average CGPA: 8.75", text)
        self.assertIn("Student deleted successfully!", text)
        self.assertIn("Average CGPA: 9.00", text)

    def test_average_with_no_students_via_menu(self):
        self.assertIn("No student records available!", self.run_session(["6", "7"]))

    def test_display_with_no_students_via_menu(self):
        self.assertIn("No students found!", self.run_session(["2", "7"]))

    def test_non_numeric_roll_in_menu(self):
        text = self.run_session(["3", "abc", "5", "xyz", "7"])
        self.assertEqual(text.count("Invalid input!"), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
