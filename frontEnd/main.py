import tkinter as tk
from ui.student_form import build_student_ui  # Adjust path if needed

root = tk.Tk()
root.title("Grade System")

build_student_ui(root)

root.mainloop()  

