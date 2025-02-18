

class PhonemicToneLanguages:
    def __init__(self, name, type, classes):
        self.name = name
        self.type = type
        self.classes = classes

    def show(self):
        print(f'{self.name} is a {self.type} and has {self.classes} classes')

japanese = PhonemicToneLanguages('japanese', 'pitch accent', '2')
japanese.show()
print(f'Japanese has \033[36m{japanese.type}\033[0m')