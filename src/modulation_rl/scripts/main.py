"""P0 training entrypoint; explicit budgets and versioned checkpoints."""
import sys
from p0_runner import main

if __name__ == '__main__':
    sys.argv.insert(1, 'train')
    main()
