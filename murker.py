#!/usr/bin/env python3

import os
import sys
import random

# Helpers
#########

def debug(*args, **kwargs):
    if 'DEBUG' in os.environ:
        print(*args, file=sys.stderr, **kwargs)

def chance(p):
    return random.uniform(0.0, 1.0) < p

def sign(x):
    if x < 0:
        return -1
    else:
        return 1

class Point:
    def __init__(self, x):
        self.x = x

    def __repr__(self):
        return f"({self.x})"


# Entity
########

class Entity:
    id_counter = 0
    entity_index = {}
    component_index = {}

    def __init__(self, *types):
        self.id = self.__class__.id_counter
        self.__class__.id_counter += 1
        self.components = []
        self.__class__.entity_index[self.id] = self
        for t in types:
            self.attach(t)

    def __repr__(self):
        s = "<"
        if self.get_component(Nameable):
            s += self.get_component(Nameable).name
        else:
            s += "Entity"
        s += f" id={self.id}"
        s += ">"
        return s

    def attach(self, component):
        component.set_owner(self)
        self.components.append(component)
        if type(component) not in self.__class__.component_index:
            self.__class__.component_index[type(component)] = []
        self.__class__.component_index[type(component)].append(self)

    def detach(self, component_type):
        for c in self.components:
            if isinstance(c, component_type):
                c.set_owner(None)
                self.components.remove(c)
                self.__class__.component_index[component_type].remove(self)
                return

    def update(self, event):
        tmp = event
        for c in self.components:
            debug(f"    {self}: {type(event).__name__} event → {type(c).__name__} component")
            tmp = c.update(tmp)
            if tmp == None:
                return

    def get_component(self, component_type):
        try:
            return next(c for c in self.components if type(c) == component_type)
        except StopIteration:
            return None

    @classmethod
    def all(cls):
        return list(cls.entity_index.values())

    @classmethod
    def filter(cls, c):
        return cls.component_index.get(c, [])

    @classmethod
    def get(cls, eid):
        return cls.entity_index.get(eid)


# Events
########

class Event:
    pass

class Turn(Event):
    pass

class Move(Event):
    def __init__(self, destination):
        self.destination = destination

class Attack(Event):
    def __init__(self, damage):
        self.damage = damage


# Components
############

class Component:
    def __init__(self):
        self.entity = None

    def set_owner(self, entity):
        self.entity = entity

    def update(self, event):
        return event

class Nameable(Component):
    def __init__(self, name):
        super().__init__()
        self.name = name

class Position(Component):
    def __init__(self, point):
        super().__init__()
        self.point = point

    def update(self, event):
        if type(event) == Move:
            old_pos = self.point
            self.point = event.destination
            print(f"{self.entity} moves {old_pos} → {event.destination}")
        return event

class Destructible(Component):
    def __init__(self, max_hp, hp = None):
        super().__init__()
        self.max_hp = max_hp
        self.hp = hp or self.max_hp

    def alive(self):
        return self.hp > 0

    def modify_hp(self, amount):
        if not self.alive():
            return
        self.hp = min(self.hp + amount, self.max_hp)
        if amount > 0:
            verb = "healed"
        elif amount < 0:
            verb = "took"
        print(f"{self.entity} {verb} {abs(amount)} damage (hp: {self.hp}/{self.max_hp})")
        if not self.alive():
            print(f"{self.entity} died!")
            self.entity.detach(Actor)

    def update(self, event):
        if type(event) == Attack:
            self.modify_hp(-event.damage)
        return event

class Attacker(Component):
    def __init__(self, accuracy, damage):
        super().__init__()
        self.accuracy = accuracy
        self.damage = damage

    def attack(self, target):
        print(f"{self.entity} attacks {target}")
        if chance(self.accuracy):
            target.update(Attack(self.damage))
        else:
            print(f"{self.entity} misses")


class Defender(Component):
    def __init__(self, evasion):
        super().__init__()
        self.evasion = evasion

    def update(self, event):
        if type(event) == Attack:
            if chance(self.evasion):
                print(f"{self.entity} evades the attack")
                return
            else:
                print(f"{self.entity} is hit")
        return event

class Actor(Component):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def update(self, event):
        if type(event) == Turn:
            self.controller.act(self.entity)
        return event

# Simple Actor controller
class BerserkAI:
    def act(self, me):
        enemies = [x for x in Entity.filter(Actor) if x != me and x.get_component(Destructible).alive()]
        if len(enemies) == 0:
            print(f"{me} sees no enemy")
            return
        my_pos = me.get_component(Position).point
        def closeness(e):
            return abs(e.get_component(Position).point.x - my_pos.x)
        closest_enemy = min(enemies, key=closeness)
        diff = closest_enemy.get_component(Position).point.x - my_pos.x
        assert(diff != 0)
        if abs(diff) == 1:
            me.get_component(Attacker).attack(closest_enemy)
        else:
            destination = my_pos.x + sign(diff)
            me.update(Move(Point(destination)))


# Example
#########

try:
    nr_goblins = int(sys.argv[1])
except IndexError:
    nr_goblins = 10
for i in range(nr_goblins):
    Entity(
        Nameable("Goblin"),
        Position(Point(3*i)),
        Attacker(0.7, 2),
        Defender(0.35),
        Destructible(10),
        Actor(BerserkAI()),
    )

print("Entities:")
for e in Entity.all():
    print(f"* {e}")

# Turn order "system"
turn_order = Entity.filter(Actor)
random.shuffle(turn_order)
while True:
    entity = turn_order.pop(0)
    print(f"\nTurn: {entity}")
    entity.update(Turn())
    for x in turn_order:
        if not x.get_component(Actor):
            turn_order.remove(x)
    if len(turn_order) == 0:
        print(f"\nThe victor is {entity}!")
        exit()
    turn_order.append(entity)
