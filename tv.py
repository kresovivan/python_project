# класс tv

class TV():
    def __init__(self):
        self.isOn = False
        self.isMuted = False
        # произвольный список каналов по умолчанию
        self.channelList = [2,4,5,7,9,11,20,36,44,54,65]
        self.nChannels = len(self.channelList)
        self.channelIndex = 0
        self.VOLUME_MINIMUM - 0 # константа
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
            self.isMuted = False #Изменение громкости включает звук, если тот отключен

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
            print('   TV is: On')
            print('   Channel is:', self.channelList[self.channelIndex])
            if self.isMuted:
                print('   Volume is:', self.volume, '(sound is muted)')
            else:
                print('   Volume is:', self.volume)
        else:
            print('   TV is: Off')


