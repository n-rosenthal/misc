from __future__ import annotations

import functools
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Iterable, TypeVar

try:
    from typing import Self  # Python 3.11+
except ImportError:
    from typing_extensions import Self

__all__ = ["Specification"]

T = TypeVar("T")


class SpecificationMeta(ABCMeta):
    """
    Metaclass that automatically decorates `is_satisfied_by` with the logging decorator.
    """
    def __new__(
        cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any]
    ) -> SpecificationMeta:
        _class = super().__new__(cls, name, bases, namespace)
        # Decorate is_satisfied_by if both methods exist and auto_log is not disabled
        if (
            hasattr(_class, "is_satisfied_by")
            and hasattr(_class, "log")
            and getattr(_class, "_auto_log", True)
        ):
            _class.is_satisfied_by = _class._log(_class.is_satisfied_by)
        return _class


class Specification(Generic[T], metaclass=SpecificationMeta):
    """
    Base class for the predicate-based specification pattern.

    Subclasses must implement `is_satisfied_by`. Override `description` to provide
    a human-readable rule. Set `_include_candidate_in_error = False` to disable
    appending the candidate value to error messages.

    IMPORTANT: Subclasses **must** call `super().__init__()` in their own `__init__`
    to ensure the error dictionary is properly initialized.
    """
    description = "No description provided."
    _include_candidate_in_error = True
    _auto_log = True  # Set to False on a subclass to disable automatic logging

    def __init__(self) -> None:
        self._last_errors: dict[str, str] = {}

    @classmethod
    def _log(
        cls, func: Callable[[Specification[T], T], bool]
    ) -> Callable[[Specification[T], T], bool]:
        """Decorator that resets errors and logs failure."""
        @functools.wraps(func)
        def wrapper(self: Specification[T], candidate: T) -> bool:
            self._last_errors = {}  # fresh error dict for this call
            result = func(self, candidate)
            self._log_failure(result, candidate)
            return result
        return wrapper

    def _log_failure(self, result: bool, candidate: T) -> None:
        """Record an error message when validation fails, optionally including the candidate."""
        if not result:
            msg = self.description
            if self._include_candidate_in_error:
                msg += f" (got: {candidate!r})"
            self._last_errors[self.class_name] = msg

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """Evaluate whether the candidate satisfies this specification."""
        raise NotImplementedError

    @property
    def class_name(self) -> str:
        return self.__class__.__name__

    @property
    def errors(self) -> dict[str, str]:
        """
        Errors from the most recent call to `is_satisfied_by`, `validate`, etc.
        Returns a copy to prevent accidental modification.
        """
        return self._last_errors.copy()

    def explain_failure(self, candidate: T) -> str:
        """
        Return a human-readable explanation of why the candidate fails this spec.
        If the candidate passes, returns an empty string.
        """
        if self.is_satisfied_by(candidate):
            return ""
        # errors already populated by the call above
        return "\n".join(f"{k}: {v}" for k, v in self._last_errors.items())

    def validate(self, candidate: T) -> bool:
        """Alias for `is_satisfied_by` (useful for naming consistency)."""
        return self.is_satisfied_by(candidate)

    def validate_or_raise(self, candidate: T, exception_cls=ValueError) -> None:
        """
        Validate and raise an exception with the error messages if validation fails.
        """
        if not self.is_satisfied_by(candidate):
            raise exception_cls(self.explain_failure(candidate))

    # Logical operators
    def __and__(self, other: Specification[T]) -> _AndSpecification[T]:
        return _AndSpecification(self, other)

    def __or__(self, other: Specification[T]) -> _OrSpecification[T]:
        return _OrSpecification(self, other)

    def __invert__(self) -> _NotSpecification[T]:
        return _NotSpecification(self)

    def __call__(self, candidate: Any) -> bool:
        return self.is_satisfied_by(candidate)

    def __repr__(self) -> str:
        return f"<{self.class_name}: {self.description}>"

    # Factory methods for building composites from iterables
    @classmethod
    def all_of(cls, specs: Iterable[Specification[T]]) -> Specification[T]:
        """Combine multiple specifications with logical AND."""
        specs = list(specs)
        if not specs:
            raise ValueError("all_of requires at least one specification")
        result = specs[0]
        for spec in specs[1:]:
            result &= spec
        return result

    @classmethod
    def any_of(cls, specs: Iterable[Specification[T]]) -> Specification[T]:
        """Combine multiple specifications with logical OR."""
        specs = list(specs)
        if not specs:
            raise ValueError("any_of requires at least one specification")
        result = specs[0]
        for spec in specs[1:]:
            result |= spec
        return result


class _AndOrSpecification(Specification[T]):
    """Base class for AND/OR composite specifications."""
    def __init__(self, spec_a: Specification[T], spec_b: Specification[T]) -> None:
        super().__init__()
        self._specs = (spec_a, spec_b)


class _AndSpecification(_AndOrSpecification[T]):
    """Logical AND of two specifications."""

    def is_satisfied_by(self, candidate: T) -> bool:
        # Evaluate first
        if not self._specs[0].is_satisfied_by(candidate):
            self._last_errors.update(self._specs[0].errors)
            return False
        # First passed, evaluate second
        if not self._specs[1].is_satisfied_by(candidate):
            self._last_errors.update(self._specs[1].errors)
            return False
        return True


class _OrSpecification(_AndOrSpecification[T]):
    """Logical OR of two specifications."""

    def is_satisfied_by(self, candidate: T) -> bool:
        # Evaluate first
        if self._specs[0].is_satisfied_by(candidate):
            return True
        # First failed, evaluate second
        if self._specs[1].is_satisfied_by(candidate):
            return True
        # Both failed
        self._last_errors.update(self._specs[0].errors)
        self._last_errors.update(self._specs[1].errors)
        return False


class _NotSpecification(Specification[T]):
    """Logical NOT of a specification."""

    description_format = "NOT({0})"

    def __init__(self, spec: Specification[T]) -> None:
        super().__init__()
        self._spec = spec
        self.description = self.description_format.format(spec.description)

    def _log_failure(self, result: bool, candidate: T) -> None:
        """Record failure when the inner spec succeeded (so NOT fails)."""
        if not result:  # NOT failed because inner succeeded
            msg = f"Expected to NOT satisfy: {self._spec.description}"
            if self._include_candidate_in_error:
                msg += f" (got: {candidate!r})"
            self._last_errors[self.class_name] = msg

    def is_satisfied_by(self, candidate: T) -> bool:
        inner = self._spec.is_satisfied_by(candidate)
        result = not inner
        if not result:
            self._log_failure(result, candidate)
        return result


# ----------------------------------------------------------------------
# Example parametric specifications using dataclasses
# ----------------------------------------------------------------------
@dataclass
class GreaterThan(Specification[int]):
    threshold: int
    description: str = field(init=False)

    def __post_init__(self):
        super().__init__()  # crucial: initialize base class
        self.description = f"Value greater than {self.threshold}"

    def is_satisfied_by(self, candidate: int) -> bool:
        return candidate > self.threshold


@dataclass
class NonEmptyString(Specification[str]):
    description: str = "Non-empty string"

    def __post_init__(self):
        super().__init__()  # crucial: initialize base class

    def is_satisfied_by(self, candidate: str) -> bool:
        return bool(candidate and candidate.strip())


# ----------------------------------------------------------------------
# Demonstration
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Simple specs
    gt5 = GreaterThan(5)
    gt10 = GreaterThan(10)
    non_empty = NonEmptyString()
    print(non_empty)

    # Composition
    between_5_and_10 = gt5 & ~gt10  # >5 and not >10 -> 5 < x <= 10
    print(between_5_and_10)                     # <_AndSpecification: ...>
    print(between_5_and_10(7))                  # True
    print(between_5_and_10(12))                 # False
    print(between_5_and_10.explain_failure(12)) # Error messages

    # Using all_of / any_of
    specs = [gt5, ~gt10]
    combined = Specification.all_of(specs)
    print(combined(7))   # True

    # Validate and raise
    try:
        between_5_and_10.validate_or_raise(3)
    except ValueError as e:
        print("Validation failed:", e)

    # Error aggregation in OR
    faulty_spec = gt5 | (GreaterThan(100) & GreaterThan(50))  # nonsense, but for demo
    print(faulty_spec(1))   # False (both branches fail)
    print(faulty_spec.errors)  # Errors from all failing children