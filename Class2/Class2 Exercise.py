class Animal:
    def __init__(self, name, alive, appetite):
        self.name = name
        self.alive = alive
        self.appetite = appetite

class Dog(Animal):
    def __init__(self, dog_name, dog_breed, alive, is_funny, likes_potatoes):
        self.name = dog_name
        self.breed = dog_breed
        self.alive = alive
        self.appetite = "Carnivore"
        self.funny = is_funny
        self.likes_potatoes = likes_potatoes

class Bird(Animal):
    def __init__(self, bird_name, bird_breed, alive, has_three_legs, is_5_foot_tall):
        self.name = bird_name
        self.breed = bird_breed
        self.alive = alive
        self.appetite = "Herbivore"
        self.has_three_legs = has_three_legs
        self.five_ft = is_5_foot_tall

class Giraffe(Animal):
    def __init__(self, giraffe_name, alive, can_wield_sword, type_3_diabetes):
        self.name = giraffe_name
        self.alive = alive
        self.appetite = "Herbivore"
        self.can_wield_sword = can_wield_sword
        self.type_3_diabetes = type_3_diabetes

dog = Dog("Greg", "Boxer", True, False, True)
bird = Bird("Terry", "Peacock", False, False, True)
giraffe = Giraffe("Henry", False, True, True)

print(f'''I have a dog named {dog.name} who is a {dog.breed}. I also have a bird {bird.name} and giraffe {giraffe.name}. Last week I
asked if {bird.name} was alive and my computer said "{bird.alive}". It is also {bird.five_ft} that my bird if five foot tall. Also,
 {giraffe.name} said it is {giraffe.type_3_diabetes} that he has diabetes. Also, it's {dog.funny} that {dog.name} is funny.''')