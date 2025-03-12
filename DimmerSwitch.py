#Класс DimmerSwitch
class DimmerSwitch():
    def __init__(self, label):
        self.label = label
        self.switchIsOn = False
        self.brightness = 0

    def turnOn(self):
        self.switchIsOn = True

    def turnOff(self):
        self.switchIsOn = False

    def raiseLevel(self):
        if self.brightness < 10:
            self.brightness = self.brightness + 1

    def lowerLevel(self):
        if self.brightness > 0:
            self.brightness = self.brightness - 1
    #Дополнительный метод для отладки
    def show(self):
        print('Label:', self.label)
        print('Switch is on?',  self.switchIsOn)
        print('Brightness is:', self.brightness)


oDimmer1 = DimmerSwitch('Dimmer1')
oDimmer1.turnOn()
oDimmer1.raiseLevel()
oDimmer1.raiseLevel()
oDimmer1.show()


oDimmer2 = DimmerSwitch('Dimmer2')
oDimmer2.turnOn()
oDimmer2.raiseLevel()
oDimmer2.raiseLevel()
oDimmer2.raiseLevel()
oDimmer2.show()

oDimmer3 = DimmerSwitch('Dimmer3')
oDimmer3.show()
