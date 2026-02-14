"""
    [specification pattern]
    
    A `Predicate` is a function that returns a boolean value.
"""

from typing import Callable
from dataclasses import dataclass

from datetime import datetime;

class Predicate:
    def __init__(self, fn: Callable):
        self.fn = fn;

    def __and__(self, other: "Predicate") -> "Predicate":
        return Predicate(fn=(self.fn and other.fn))
    
    def __land__(self, other: "Predicate") -> "Predicate":
        return Predicate(fn=(self.fn and other.fn))
        
    
    def __or__(self, other: "Predicate") -> "Predicate":
        return Predicate(fn=(self.fn or self.fn))
    
    def __call__(self, *args):
        print(args, self.fn.__name__)
        return self.fn(*args)

@dataclass
class User:
    name: str
    staff: bool
    admin: bool
    active: bool
    
    def __str__(self) -> str:
        return u.name;

def log(msg: str) -> None:
    print( str(datetime.now()) + " " + msg)

def is_active(u: User) -> bool:
    if u.active:
        log(str(u) + " está ativo.")
        return True
    else:
        log(str(u) + " não está ativo")
        return False

def is_admin(u: User) -> bool:
    if u.admin:
        log(str(u) + " é administrador.")
        return True;
    else:
        log(str(u) + " não é administrador.")
        return False;

def is_staff(u: User) -> bool:
    if u.staff:
        log(str(u) + " é gerente.")
        return True;
    else:
        log(str(u) + " não é gerente.")
        return False;

users: list[User] = [
    User(name="john_h",     staff=False, admin=False, active=True),
    User(name="isabela_t",  staff=True,  admin=False, active=True),
    User(name="rosalind_b", staff=True,  admin=True,  active=True),
    User(name="meredith_g", staff=False, admin=False, active=False),
]

is_user_active: Predicate = Predicate(fn=is_active)
is_user_staff:  Predicate = Predicate(fn=is_staff)
is_user_admin:  Predicate = Predicate(fn=is_admin)
rule:           Predicate = is_user_admin or (is_user_active)


for u in users: rule(u)
