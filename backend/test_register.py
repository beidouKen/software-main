import requests
import sys

url = "http://localhost:8000/api/auth/register/admin"
data = {
    "username": "testadmin_check_2",
    "password": "password123",
    "name": "Test Admin"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
