import tkinter as tk
from tkinter import messagebox
from api.students import get_students, add_student

def build_student_ui(root):
    frame = tk.Frame(root)
    frame.pack(pady=10)

    # Form Labels and Inputs
    tk.Label(frame, text="First Name").grid(row=0, column=0)
    first = tk.Entry(frame)
    first.grid(row=0, column=1)

    tk.Label(frame, text="Last Name").grid(row=1, column=0)
    last = tk.Entry(frame)
    last.grid(row=1, column=1)

    tk.Label(frame, text="Date of Birth").grid(row=2, coloumn=0)
    dob = tk.Entry(frame)
    dob.grid(row=2, column=1)
    
    tk.Lable(frame, )

    # Submit Button Logic
    def submit():
        response = add_student({
            "first_name": first.get(),
            "last_name": last.get(),
            "date_of_birth": "2005-01-01",  # You can change this to a user input
            "gender": "M"  # Same here
        })
        if response.status_code == 201:
            messagebox.showinfo("Success", "Student Added")
        else:
            messagebox.showerror("Error", "Something went wrong")

    # Submit Button (fixed placement and spelling)
    tk.Button(frame, text="Submit", command=submit).grid(row=2, columnspan=2)

    return frame
