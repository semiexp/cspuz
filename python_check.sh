CHECK_DIR="cspuz tests bench"

yapf -d -r $CHECK_DIR
flake8 $CHECK_DIR
