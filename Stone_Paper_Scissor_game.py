# This is a simple Stone-Paper-Scissors game
import random
a=input("Entre your choice (stone/paper/scissor): ") # The user inputs their choice
b=random.choice(["stone","paper","scissor"]) # The computer randomly selects its choice
print(f"computer choice: {b} \n your choice: {a}")
    # The game determines the winner based on standard rules:
if a==b: # - Same choices result in a tie
    print("tie")
elif a=="stone" and b=="scissor":  # - Stone beats Scissors
    print("you win")
elif a=="paper" and b=="stone":  # - Paper beats Stone
    print("you win")
elif a=="scissor" and b=="paper":  # - Scissors beats Paper
    print("you win")
else:
    print("you lose")
