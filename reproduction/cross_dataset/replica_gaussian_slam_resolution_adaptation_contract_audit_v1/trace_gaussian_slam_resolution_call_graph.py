import sys
from audit_driver import main
if __name__ == "__main__":
    sys.argv[1:] = ["--stage", "STATIC_CALL_GRAPH"]
    main()
