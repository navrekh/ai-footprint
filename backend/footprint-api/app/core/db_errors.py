from sqlalchemy.exc import IntegrityError


def is_unique_violation(exc: IntegrityError, constraint_name: str) -> bool:
    """True only when exc is a unique-constraint/index violation for the
    given constraint or index name specifically - never a generic "some
    IntegrityError happened" - so an unrelated integrity error is never
    mistaken for a resolvable conflict.
    """
    return constraint_name in str(exc.orig)
