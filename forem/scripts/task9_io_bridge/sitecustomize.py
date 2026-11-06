"""Opt-in, explicitly authorized task9 I/O monitoring compatibility bootstrap."""
import os
if os.environ.get('TASK9_IO_BRIDGE_AUTH'):
    try:
        from task9_io_bridge_impl import install
        install()
    except BaseException:
        import traceback,sys
        traceback.print_exc(file=sys.stderr)
        # Python normally ignores sitecustomize errors. A requested bridge must
        # fail closed rather than silently start an unadapted native guardian.
        os._exit(78)
