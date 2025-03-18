import psutil

battery = psutil.sensors_battery()
plugged = battery.power_plugged
percent = battery.percent


    # pip install py-notifier
    # pip install win10toa

    print(percent)