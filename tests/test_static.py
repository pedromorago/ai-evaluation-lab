"""Static checks on generated files: what runs, and which tests assert anything."""

from aievals.static import check

SAFE = '''
import pytest
from decimal import Decimal
from checkout import price_cart, CartError

def helper(q):
    assert q.total > 0

def test_asserts():
    assert 1 + 1 == 2

def test_raises_only():
    with pytest.raises(CartError):
        price_cart([], {}, today=None, shipping="drone")

def test_through_helper():
    helper(object())

def test_nothing():
    price_cart([], {}, today=None)
'''


def test_finds_tests_without_assertions():
    c = check("test_x.py", SAFE)
    assert c.tests == ["test_asserts", "test_raises_only", "test_through_helper", "test_nothing"]
    assert c.no_assertion == ["test_nothing"]
    assert c.runnable


def test_pytest_raises_is_an_assertion():
    assert "test_raises_only" not in check("test_x.py", SAFE).no_assertion


def test_syntax_errors_are_not_run():
    c = check("test_x.py", "def test_x(:\n    pass\n")
    assert c.syntax_error and not c.runnable


def test_file_and_process_access_is_not_run():
    for source in [
        "import os\ndef test_x():\n    assert os.getcwd()\n",
        "import subprocess\ndef test_x():\n    assert subprocess.run(['ls'])\n",
        "from pathlib import Path\ndef test_x():\n    assert Path('.').exists()\n",
        "def test_x():\n    assert open('x', 'w')\n",
        "def test_x():\n    assert ().__class__.__bases__\n",
    ]:
        c = check("test_x.py", source)
        assert c.unsafe and not c.runnable, source
