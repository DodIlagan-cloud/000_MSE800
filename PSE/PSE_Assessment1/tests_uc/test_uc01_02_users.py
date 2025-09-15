import pytest
from user_repo import UserRepo, RepoError

def test_uc01_register_new_user(temp_db):
    ur = UserRepo()
    email = "hermione@hogwarts.example"
    full_name = "Hermione Granger"
    u = ur.auth_signup(email=email, full_name=full_name, password="Alohomora1!", role="customer")
    assert u.email == email
    assert u.full_name == full_name

def test_uc01_register_duplicate_email(temp_db):
    ur = UserRepo()
    email = "harry@hogwarts.example"
    ur.auth_signup(email=email, full_name="Harry Potter", password="Nimbus2000!", role="customer")
    with pytest.raises(RepoError):
        ur.auth_signup(email=email, full_name="Harry J. Potter", password="NewPass1!", role="customer")

def test_uc02_login_success(temp_db):
    ur = UserRepo()
    email = "ron@hogwarts.example"
    pwd = "Weasley#1"
    ur.auth_signup(email=email, full_name="Ron Weasley", password=pwd, role="customer")
    u = ur.auth_login(email, pwd)
    assert u and u.email == email

def test_uc02_login_wrong_password(temp_db):
    ur = UserRepo()
    email = "ginny@hogwarts.example"
    ur.auth_signup(email=email, full_name="Ginny Weasley", password="BatBogey1!", role="customer")
    u = ur.auth_login(email, "bad-password")
    assert u is None
