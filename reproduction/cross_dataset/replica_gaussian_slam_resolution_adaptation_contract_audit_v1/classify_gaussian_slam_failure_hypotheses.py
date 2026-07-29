import sys
from audit_driver import main
if __name__ == "__main__":
    sys.argv[1:] = ["--stage", "FAILURE_HYPOTHESIS_CLASSIFICATION"]
    main()
