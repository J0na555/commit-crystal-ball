import sys
from crystal_ball.cli import app

if __name__ == "__main__":
    # argv[0] is the __main__.py path.
    sys.argv[0] = "crystal_ball"
    app()
