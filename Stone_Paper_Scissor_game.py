# This is a simple Stone-Paper-Scissors game
import random

# User input with cleanup
a = input("Enter your choice (stone/paper/scissor): ").strip().lower()

# Validate input
if a not in ["stone", "paper", "scissor"]:
    print("Invalid input. Please choose stone, paper, or scissor.")
    exit()

# Computer's random choice
b = random.choice(["stone", "paper", "scissor"]) 

# Display choices
print(f"Computer choice: {b} \nYour choice: {a}")

# Determine winner
if a == b:
    print("It's a tie!")
elif (a == "stone" and b == "scissor") or \
     (a == "paper" and b == "stone") or \
     (a == "scissor" and b == "paper"):
    print("You win!")
else:
    print("You lose!")
