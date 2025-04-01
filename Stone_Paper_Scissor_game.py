# This is a simple Stone-Paper-Scissors game
import random

# The user inputs their choice
a=input("Entre your choice (stone/paper/scissor): ")

# The computer randomly selects its choice
b=random.choice(["stone","paper","scissor"]) 

# print both the choices
print(f"computer choice: {b} \n your choice: {a}")

# The game determines the winner based on standard rules:

# - Same choices result in a tie
if a==b:
    print("tie")
# - Stone beats Scissors
elif a=="stone" and b=="scissor": 
    print("you win")
# - Paper beats Stone
elif a=="paper" and b=="stone":
    print("you win")
# - Scissors beats Paper
elif a=="scissor" and b=="paper":
    print("you win")
else:
    print("you lose")
