class Entity:
    id_counter = 0
    entity_index = {}
    component_index = {}

    def __init__(self):
        self.id = self.id_counter
        self.id_counter += 1
        self.components = []
        self.entity_index[self.id] = self

    def attach(self, component):
        component.set_owner(self)
        self.components.append(component)
        if type(component) not in self.component_index:
            self.component_index[type(component)] = []
        self.component_index[type(component)].append(self)

    def update(self, event):
        tmp = event
        for c in self.components:
            tmp = c.update(tmp)

    def get_component(self, component_type):
         return next(c for c in self.components if type(c) == component_type)

    @classmethod
    def filter(cls, component_types):
        entities = cls.component_index.get(component_type)
        return entities if entities is not None else []

    @classmethod
    def get(cls, eid):
        return cls.entity_index.get(eid)

class Point:
    def __init__(self, x, y, z = 0):
        self.x = x
        self.y = y
        self.z = z

class Event:
    pass

class Move(Event):
    def __init__(self, destination):
        self.destination = destination

class InitAttack(Event):
    def __init__(self, target):
        self.target = target

class Attack(Event):
    def __init__(self, damage):
        self.damage = damage

class CanSee(Event):
    def __init__(self, who):
        self.who = who

class Component:
    def __init__(self):
        self.owner = None

    def set_owner(self, entity):
        self.owner = entity

class Position(Component):
    def __init__(self, point):
        super().__init__()
        self.point = point

    def update(self, event):
        if type(event) == Move:
            old_pos = self.point
            self.point = event.destination
            name = self.owner.get_component(BerserkAI).name
            print(f"{name} moves {old_pos} → {event.destination}")
        return event

class Destructible(Component):
    def __init__(self, hp):
        super().__init__()
        self.hp = hp

    def alive(self):
        return self.hp > 0

    def update(self, event):
        if type(event) == Attack:
            self.hp -= event.damage
            name = self.owner.get_component(BerserkAI).name
            print(f"{name} took {event.damage} damage ({self.hp} remaining)")
            if not self.alive():
                print(f"{name} died!")
        return event

class Attacker(Component):
    def __init__(self, damage):
        super().__init__()
        self.damage = damage

    def update(self, event):
        return event

class Actor(Component):
    def update(self, event):
        if type(event) == InitAttack:
            attacker = self.owner.get_component(Attacker)
            name = self.owner.get_component(BerserkAI).name
            target_name = event.target.get_component(BerserkAI).name
            print(f"{name} attacks {target_name}!")
            event.target.update(Attack(attacker.damage))
        return event

class PlayerControlled(Component):
    pass

class BerserkAI(Component):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def update(self, event):
        if type(event) == CanSee:
            event = InitAttack(event.who)
        return event


orc = Entity()
orc.attach(Destructible(10))
orc.attach(Position(Point(0,0)))
orc.attach(BerserkAI("orc"))
orc.attach(Attacker(3))
orc.attach(Actor())

goblin = Entity()
goblin.attach(Destructible(13))
goblin.attach(Position(Point(0,1)))
goblin.attach(BerserkAI("goblin"))
goblin.attach(Attacker(2))
goblin.attach(Actor())

def is_alive(entity):
    return entity.get_component(Destructible).alive()

while is_alive(orc) and is_alive(goblin):
    orc.update(CanSee(goblin))
    if is_alive(goblin) and is_alive(orc):
        goblin.update(CanSee(orc))
