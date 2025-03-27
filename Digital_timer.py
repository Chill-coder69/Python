import time
a=input("timer duration : ")
b=int(a.split(" ")[0])
if "sec" in a :
    for y in range(b,0,-1):
        sec = int(y%60)
        min = int(y/60)
        hr = int(y/3600)
        print(f"{hr:02}:{min:02}:{sec:02}" , end="\r")
        time.sleep(1)
if "min" in a :
    for y in range(b*60,0,-1):
        sec = int(y%60)
        min = int(y/60)
        hr = int(y/3600)
        print(f"{hr:02}:{min:02}:{sec:02}" , end="\r")
        time.sleep(1)
if "hr" in a :
    for y in range(b*3600,0,-1):
        sec = int(y%60)
        min = int(y/60)
        hr = int(y/3600)
        print(f"{hr:02}:{min:02}:{sec:02}" , end="\r")
        time.sleep(1)
print("TIME'S UP")
