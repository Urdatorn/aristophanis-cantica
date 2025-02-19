class Car:
    def __init__(self, brand, model):
        self.brand = brand
        self.model = model

    def printer(self):
        print(f'My name is {self}')

toyota = Car('Toyota', 'Prius')
toyota.printer()
