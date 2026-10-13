# Student Management System

A console-based Student Management System written in **Python 3**, converted and improved from an earlier C++ version. Student records are stored in a simple CSV-formatted text file, so they are kept between runs.

> SCPL (Structured and Computer Programming Laboratory) Mini Project, Academic Year 2026–27

## 1. Project Overview

The program shows a menu and lets the user add, view, search, update and delete student records, and calculate the average CGPA. It uses only the Python standard library.

## 2. Problem Statement

Keeping student records on paper or in loose files makes searching slow, updates error-prone and calculations (such as an average CGPA) repetitive. These are general problems of manual record keeping. This project provides a small program that keeps the records in one place, checks the data entered, and saves it automatically.

## 3. Objectives

1. Simplify student record management.
2. Add, view, search, update and delete records.
3. Validate student information (unique roll number, CGPA from 0 to 10).
4. Calculate the average CGPA automatically.
5. Store records permanently using file handling.

## 4. Features

- Menu-driven interface with 7 options
- Unique, positive-integer roll numbers (duplicates rejected)
- Names and branches may contain spaces (for example `Anil Kumar Rao`)
- CGPA validated to be a number from 0 to 10
- Updates are validated first, so a bad input never half-changes a record
- Aligned table for displaying records (column widths adapt to the data)
- Average CGPA shown to two decimal places; empty list handled safely
- Records saved after every add / update / delete and loaded at start-up
- Missing data file, blank lines, malformed rows and duplicate rows in the file are handled without crashing
- Invalid menu choices and non-numeric input do not stop the program

## 5. Technologies Used

| Item | Used |
|---|---|
| Language | Python 3 (tested with 3.12) |
| Storage | Local text file in CSV format (`students.txt`) |
| Libraries | Standard library only: `csv`, `os`, `sys`, `math` |
| Testing | `unittest` |
| Concepts | Classes, objects, functions, loops, conditions, lists, file handling, exception handling |

## 6. Project Structure

```
Student-Management-System/
├── main.py                       # the complete application
├── students.txt                  # data file (starts with only a header row)
├── README.md
├── requirements.txt              # no external packages needed
├── test_student_management.py    # unit tests (unittest)
└── screenshots/
    ├── 01_main_menu.png ... 08_data_persistence.png
    ├── generate_screenshots.py   # re-creates the screenshots from the real program
    └── unittest_output.txt       # saved output of the test run
```

## 7. Installation Requirements

- Python 3.8 or newer (https://www.python.org/downloads/)
- Nothing else. `requirements.txt` only contains comments because no external packages are used.
- (Optional) `pip install pillow` is needed only to run `screenshots/generate_screenshots.py`.

## 8. How to Run

Open a terminal (Command Prompt on Windows) in the project folder:

```
python main.py
```

On Windows you can also try `py main.py`. To use a different data file: `python main.py other_file.txt`.

## 9. Using Each Menu Option

| Option | What to do |
|---|---|
| 1. Add Student | Enter roll number, full name, branch and CGPA. A duplicate roll number or a CGPA outside 0–10 is rejected. |
| 2. Display All Students | Shows every record in a table, or a message if there are none. |
| 3. Search Student | Enter a roll number to see the full record. |
| 4. Update Student | Enter the roll number, then new name, branch and CGPA. Press **Enter** to keep a current value. If any new value is invalid, nothing is changed. |
| 5. Delete Student | Enter the roll number of the record to remove. |
| 6. Calculate Average CGPA | Average = sum of all CGPAs / number of students, shown with two decimals. |
| 7. Exit | Closes the program. |

## 10. Data Storage

Records are stored in `students.txt` as CSV, one student per line:

```
roll_no,name,branch,cgpa
2,Sample Student Two,IT,8.00
```

- The C++ version wrote fields separated by spaces, so a name like `Anil Kumar` broke loading. CSV (via Python's `csv` module) keeps spaces and even commas inside names safe.
- The file is read once when the program starts and rewritten after each change. It is written to a temporary file first and then swapped in, so a failure during saving does not destroy the old file.
- If `students.txt` does not exist, the program starts with no records and creates the file on the first save.
- Rows that are malformed or repeat a roll number are skipped and reported as warnings at start-up.
- A database was not used because the project is small and the aim is to practise simple file handling.

The `Sample Student ...` names used in the screenshots and tests are **sample data only**, not real students.

## 11. Testing

```
python -m unittest -v test_student_management.py
```

The 33 tests use temporary files, so the real `students.txt` is never changed. They cover adding, duplicate roll numbers, searching (found / not found), updating, invalid CGPA (no change to the record or file), deleting, average CGPA (normal and empty list), saving and reloading, names with spaces, malformed file rows, a missing file, invalid menu choices, and restarting the program with data kept.

Result of the run saved in this project: **33 tests, 0 failures** (see `screenshots/unittest_output.txt`).

## 12. Screenshots

The images in `screenshots/` come from running the real program with scripted keyboard input. Typed answers appear in yellow. Each image shows one or two menu cycles; the menu box is shown in the first image and left out of the others to keep them compact (the program itself prints it after every action). To use your own screenshots, run `python main.py` and capture the window with the Windows Snipping Tool (Win + Shift + S).

## 13. Current Limitations

- Console only; no graphical interface
- One CSV file; no multi-user access and no login
- Search is by roll number only (not by name or branch)
- Records are displayed in the order they were added; no sorting or filtering
- No backup or export feature

## 14. Future Enhancements

- Graphical user interface
- Database integration
- Student login and administrator access
- Exporting reports
- Sorting and filtering of records
- Backup and restore

## 15. Author Information

| | |
|---|---|
| Students | Yash Dashrath (Roll No. 32), Tanmay Gunjal (Roll No. 36) |
| Department | Computer Science Engineering (CSE), Second Year, Division A |
| College | PCET's Nutan Maharashtra Institute of Engineering and Technology, Pune |
| Subject | SCPL |

