from __future__ import annotations

import functools
from abc import ABCMeta, abstractmethod
from typing import Any, Callable, Generic, TypeVar

__all__ = ["Specification"]

T = TypeVar("T")


class SpecificationMeta(ABCMeta):
    """
    Metaclass that automatically decorates `is_satisfied_by` with the logging decorator.
    """
    def __new__(cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> SpecificationMeta:
        _class = super().__new__(cls, name, bases, namespace)
        # Decorate is_satisfied_by with the logging decorator if both methods exist
        if hasattr(_class, "is_satisfied_by") and hasattr(_class, "log"):
            # Use the classmethod _log, not the instance method log
            _class.is_satisfied_by = _class._log(_class.is_satisfied_by)
        return _class  # Always return the class


class Specification(Generic[T], metaclass=SpecificationMeta):
    """
    Base class for the predicate-based specification pattern.
    """
    description = "No description provided."

    def __init__(self) -> None:
        self.errors: dict[str, str] = {}

    @classmethod
    def _log(
        cls, func: Callable[[Specification[T], T], bool]
    ) -> Callable[[Specification[T], T], bool]:
        """Decorator for error reporting."""
        @functools.wraps(func)
        def wrapper(self: Specification[T], candidate: T) -> bool:
            self.errors = {}  # reset errors
            result = func(self, candidate)
            self.log(result)
            return result
        return wrapper

    def log(self, result: bool) -> None:
        """Register an error message when validation fails."""
        if result is False:
            self.errors.update({self.class_name: self.description})

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """Evaluate whether the candidate satisfies this specification."""
        raise NotImplementedError

    @property
    def class_name(self) -> str:
        return self.__class__.__name__

    def __and__(self, spec: Specification[T]) -> _AndSpecification[T]:
        return _AndSpecification(self, spec)

    def __or__(self, spec: Specification[T]) -> _OrSpecification[T]:
        return _OrSpecification(self, spec)

    def __invert__(self) -> _NotSpecification[T]:
        return _NotSpecification(self)

    def __call__(self, candidate: Any) -> bool:
        return self.is_satisfied_by(candidate)

    def __repr__(self) -> str:
        return f"<{self.class_name}: {self.description}>"


class _AndOrSpecification(Specification[T]):
    """Base class for AND/OR composite specifications."""
    def __init__(self, spec_a: Specification[T], spec_b: Specification[T]) -> None:
        super().__init__()
        self._specs = (spec_a, spec_b)

    def _report_error(self, result: bool) -> None:
        """Collect errors from child specifications."""
        for spec in self._specs:
            self.errors.update(spec.errors)

    def is_satisfied_by(self, candidate: T) -> bool:
        results = (spec.is_satisfied_by(candidate) for spec in self._specs)
        combined = self._check(*results)
        if not combined:                     # Only collect errors when the composite fails
            self._report_error(combined)
        return combined

    @abstractmethod
    def _check(self, spec_a: bool, spec_b: bool) -> bool:
        raise NotImplementedError


class _AndSpecification(_AndOrSpecification[T]):
    def _check(self, spec_a: bool, spec_b: bool) -> bool:
        return spec_a and spec_b


class _OrSpecification(_AndOrSpecification[T]):
    def _check(self, spec_a: bool, spec_b: bool) -> bool:
        return spec_a or spec_b


class _NotSpecification(Specification[T]):
    description_format = "Expected condition to NOT satisfy: {0}"

    def __init__(self, spec: Specification[T]) -> None:
        super().__init__()
        self._spec = spec
        self.description = self.description_format.format(self._spec.description)

    def _report_error(self, inner_result: bool) -> None:
        """Report error when the inner specification succeeded (so NOT fails)."""
        if inner_result is True:  # NOT fails because inner succeeded
            self.errors.update({self._spec.class_name: self.description})

    def is_satisfied_by(self, candidate: T) -> bool:
        inner = self._spec.is_satisfied_by(candidate)
        result = not inner
        if not result:            # NOT fails -> log error
            self._report_error(inner)
        return result

class PositiveIntegerSpecification(Specification[int]):
    description = "A positive integer"

    def is_satisfied_by(self, candidate: int) -> bool:
        return candidate > 0

class SmallerThanSpecification(Specification[int]):
    description = "Smaller than 10"
    value: int
    
    def __init__(self, value: int) -> None:
        super().__init__()
        self.value = value

    def is_satisfied_by(self, candidate: int) -> bool:
        return candidate < self.value

SPEC: Specification[int] = PositiveIntegerSpecification() & SmallerThanSpecification(12)


if __name__ == '__main__':
    print(SPEC.is_satisfied_by(11))