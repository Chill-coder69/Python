# save user choice of conversion
User_input=input("what unit you want to convert into what unit : ").upper()

# detects any invalid input
if User_input not in ["C TO F","C TO K","F TO C","F TO K","K TO C","K TO F"]:
    print("the unit is invalid")
    # exit after detecting
    exit()

# take your temperature
User_temp=int(input(f"type your temp in {(User_input.split(" ")[0])} : "))

# results 
results={"C TO F": (User_temp * 9/5) + 32 ,
         "C TO K": User_temp + 273.15 , 
         "F TO C" : (User_temp - 32) * 5/9 ,
         "F TO K": ((User_temp - 32) * 5/9) + 273.15,
         "K TO C":  User_temp - 273.15 ,
         "K TO F":((User_temp - 273.15) * 9/5) + 32}

# give output
print(f"your temprature in {(User_input.split(" ")[2])} : {results[User_input]}")
