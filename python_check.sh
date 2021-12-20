CHECK_DIR="cspuz tests bench"

# yapf -d -r $CHECK_DIR
# flake8 $CHECK_DIR --ignore="H"

echo "Running black..."
black --line-length 99 $CHECK_DIR

echo "Running flake8..."
flake8 --max-line-length 99 --ignore H,E203,W503,W504 $CHECK_DIR

echo "Running mypy..."
mypy $CHECK_DIR
