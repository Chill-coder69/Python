import time
a=input("timer duration : ")           # take user input for time
b=int(a.split(" ")[0])                 # seperate out the no. from input
if "sec" in a :                        # run for seconds
    for y in range(b,0,-1):            # run in reverse
        sec = int(y%60)
        min = int(y/60)
        hr = int(y/3600)
        print(f"{hr:02}:{min:02}:{sec:02}" , end="\r") # print the timer and rewrite the previous print
        time.sleep(1)
elif "min" in a :                       # run for minutes
    for y in range(b*60,0,-1):        # run in reverse
        sec = int(y%60)
        min = int(y/60)
        hr = int(y/3600)
        print(f"{hr:02}:{min:02}:{sec:02}" , end="\r")  # print the timer and rewrite the previous print
        time.sleep(1)
elif "hr" in a :                       # run for hours
    for y in range(b*3600,0,-1):     # run in reverse
        sec = int(y%60)
        min = int(y/60)
        hr = int(y/3600)
        print(f"{hr:02}:{min:02}:{sec:02}" , end="\r") # print the timer and rewrite the previous print
        time.sleep(1)
else :
    print("Invalid input")
    exit()
print("TIME'S UP")
