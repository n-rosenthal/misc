"""
    [specification pattern]
    
    A `Predicate` is a function that returns a boolean value.
"""

from typing import Callable
from dataclasses import dataclass

class Predicate:
    def __init__(self, fn: Callable):
        self.fn = fn;

    def __and__(self, other: "Predicate") -> "Predicate":
        return Predicate(fn=(self.fn and other.fn))
    
    def __or__(self, other: "Predicate") -> "Predicate":
        return Predicate(fn=(self.fn or self.fn))
    
    def __call__(self, *args):
        return self.fn(*args)

@dataclass
class User:
    name: str
    staff: bool
    admin: bool
    active: bool

def is_active(u: User) -> bool:
    return u.active == True;

def is_admin(u: User) -> bool:
    return u.admin == True;

def is_staff(u: User) -> bool:
    return u.staff == True;

users: list[User] = [
    User(name="john_h", staff=False, admin=False, active=True),
    User(name="isabela_t", staff=True, admin=False, active=True),
    User(name="rosalind_b", staff=True, admin=True, active=True),
    User(name="meredith_g", staff=False, admin=False, active=False),
    
]

is_user_active: Predicate = Predicate(fn=lambda u: u.active == True)
is_user_staff:  Predicate = Predicate(fn=lambda u: u.staff == True)
is_user_admin:  Predicate = Predicate(fn=lambda u: u.admin == True)
rule:           Predicate = is_user_active and (is_user_staff or is_user_admin)


for u in users:
    if(rule(u)):
        print(u.name + " ok!");
    else:
        print(u.name + " está inativo.");
