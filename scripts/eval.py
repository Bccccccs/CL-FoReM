"""P0 single evaluation entrypoint; checkpoint and seed manifest are required."""
import sys
from p0_runner import main

if __name__ == '__main__':
    sys.argv.insert(1, 'eval')
    main()
