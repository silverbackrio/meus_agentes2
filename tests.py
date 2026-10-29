import os
import sys

# Garante que o projeto é achado pelo pytest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_smoke():
    assert True
