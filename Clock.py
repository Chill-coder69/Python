import datetime as dt
import time as t
import pygame as g

mp3 = "your ringtone.mp3"
def Timer():
    user_input = input("Enter the timer duration (HH:MM:SS) : ")
    h = int(user_input.split(":")[0])
    m = int(user_input.split(":")[1])
    s = int(user_input.split(":")[2])
    tt = h*3600 + m*60 + s
    for d in range(tt,0,-1):
        hr =  int(d/3600)
        min = int(d/60)%60
        sec = int(d%60)
        print(f"{hr:02}:{min:02}:{sec:02}" , end="\r")
        t.sleep(1)
    while True:
        g.mixer.init()
        g.mixer.music.load(mp3)
        g.mixer.music.play(loops=-1)
        input("Press Enter to quit.....")
        break

def Stopwatch():
    input("Press enter to start stopwatch...")
    i = 0
    while True :
        i += 1
        hr =  int(i/3600)
        min = int(i/60)%60
        sec = int(i%60)
        print(f"{hr:02}:{min:02}:{sec:02}" , end="\r")
        t.sleep(1)

def Alarm():
    running = True
    time = input("Enter the alaram time (HH:MM:SS) : ")
    while running:
        current_time = dt.datetime.now().strftime("%H:%M:%S")
        print(current_time , end="\r")
        if current_time==time:
            while running:
                g.mixer.init()
                g.mixer.music.load(mp3)
                g.mixer.music.play(loops=-1)
                input("Press Enter to quit.....")
                break
while True:
    if __name__=="__main__":
        print("---------------Welcome to clock--------------------------")
        ask = input("Enter :-\n\"A\" for alarm \n\"T\" for timer and \n\"S\" for stopwatch\n>>>>>>>>> ").lower()
        if ask == "a":
            Alarm()
        elif ask == "t":
            Timer()
        elif ask == "s":
            Stopwatch()
        else :
            print("Invalid input")
