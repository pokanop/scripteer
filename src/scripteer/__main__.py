"""Support python -m scripteer using the same installed command boundary."""

from .entrypoint import main

raise SystemExit(main())
