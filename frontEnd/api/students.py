import requests

BASE_URL = "http://127.0.0.1:8000/api/students/"

def get_students():
    return requests.get(BASE_URL).Json()

def add_student(data):
    return requests.post(BASE_URL, json=data)

def delete_student(student_id):
    return requests.delete(f"{BASE_URL} {student_id}/")

def update_student(student_id, data):
    return requests.put(f"{BASE_URL} {student_id}/", json=data)