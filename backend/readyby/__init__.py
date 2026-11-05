"""Shared, framework-free ReadyBy business logic.

This package deliberately holds no Django models or views so the core ready-by
calculation can be imported from anywhere (order placement, café discovery,
merchant dashboard) and unit tested on its own. It is the single implementation
of the ReadyBy promise — if the maths changes, it changes here.
"""