# класс tv

class TV():
    def __init__(self, brand, location): #передаем бренд и расположение телевизора
        self.brand = brand
        self.location = location
        self.isOn = False
        self.isMuted = False
        # произвольный список каналов по умолчанию
        self.channelList = [2,4,5,7,9,11,20,36,44,54,65]
        self.nChannels = len(self.channelList)
        self.channelIndex = 0
        self.VOLUME_MINIMUM = 0 # константа
        self.VOLUME_MAXIMUM = 10 # константа
        self.volume = self.VOLUME_MAXIMUM #целочисленная переменная

    def power(self):
        self.isOn = not self.isOn #переключатель

    def volumeUp(self):
        if not self.isOn:
            return
        if self.isMuted:
            self.isMuted = False #изменение громкости меняет звук, если он отключен
        if self.volume < self.VOLUME_MAXIMUM:
            self.volume = self.volume + 1

    def volumeDown(self):
        if not self.isOn:
            return
        if self.isMuted:
            self.isMuted = False
        if self.volume > self.VOLUME_MINIMUM:
            self.volume = self.volume - 1

    def channelUp(self):
        if not self.isOn:
            return
        self.channelIndex = self.channelIndex + 1
        if self.channelIndex > self.nChannels:
            self.channelIndex = 0 # После последнего канала вернуться к первому каналу

    def channelDown(self):
        if not self.isOn:
            return
        self.channelIndex = self.channelIndex - 1
        if self.channelIndex < 0:
            self.channelIndex = self.nChannels - 1 # Перед первым каналом последний

    def mute(self):
        if not self.isOn:
            return
        self.isMuted = not self.isMuted

    def setChannel(self, newChannel):
        if newChannel in self.channelList:
            self.channelIndex = self.channelList.index(newChannel) #Если newChannel нет в нашем списке каналов, то ничего не делать

    def showInfo(self):
        print()
        print('TV Status:')
        if self.isOn:
            print('   Status of TV',self.brand)
            print('   Location of TV', self.location)
            print('   TV is: On')
            print('   Channel is:', self.channelList[self.channelIndex])
            if self.isMuted:
                print('   Volume is:', self.volume, '(sound is muted)')
            else:
                print('   Volume is:', self.volume)
        else:
            print('   Status of TV', self.brand)
            print('   Location of TV', self.location)
            print('   TV is: Off')

#Создаем объекты телевизоры TV
oTV = TV('Samsung', 'Bedroom')
oTV1 = TV('Philipps', 'Family room')
oTV2 = TV('Izumrud', 'Balcony')

#Включаем телевизор и показываем статус
oTV.power()
oTV.showInfo()

#Дважды меням канал, дважды увеличиваем громкость, после этого показываем статус
oTV.channelUp()
oTV.channelUp()
oTV.volumeUp()
oTV.volumeUp()
oTV.showInfo()
oTV.setChannel(11)
oTV.volumeDown()
oTV.volumeDown()
oTV.volumeDown()
oTV.volumeDown()
oTV.showInfo()

oTV1.power()
oTV1.showInfo()
oTV1.setChannel(36)
oTV1.volumeDown()
oTV1.showInfo()

oTV2.power()
oTV2.showInfo()
oTV2.setChannel(65)
oTV2.volumeDown()
oTV2.power()
oTV2.showInfo()

