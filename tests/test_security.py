import pytest
from app.core.security import verify_identity


def test_verify_identity_dob_formats():
    assert verify_identity("16/08/2000") is True
    assert verify_identity("16-08-2000") is True
    assert verify_identity("16 08 2000") is True
    assert verify_identity("16th August 2000") is True
    assert verify_identity("August 16 2000") is True
    assert verify_identity("16 August") is True


def test_verify_identity_girlfriend_name():
    assert verify_identity("Jamirah") is True
    assert verify_identity("Najjemba") is True
    assert verify_identity("Jamirah Najjemba") is True
    assert verify_identity("najjemba jamirah") is True
    assert verify_identity("My girlfriend is Jamirah") is True


def test_verify_identity_invalid():
    assert verify_identity("John Doe") is False
    assert verify_identity("01/01/1990") is False
    assert verify_identity("hello there") is False
    assert verify_identity("12345") is False
