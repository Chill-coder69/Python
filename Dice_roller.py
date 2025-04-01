import random  # Importing the random module to generate random numbers

# Dictionary representing the dice faces using ASCII art
dice = {
    1: ("┌─────────┐", 
        "│         │", 
        "│    •    │", 
        "│         │", 
        "└─────────┘"),
    2: ("┌─────────┐", 
        "│ •       │", 
        "│         │", 
        "│       • │", 
        "└─────────┘"),
    3: ("┌─────────┐", 
        "│ •       │", 
        "│    •    │", 
        "│       • │", 
        "└─────────┘"),
    4: ("┌─────────┐", 
        "│  •   •  │", 
        "│         │", 
        "│  •   •  │", 
        "└─────────┘"),
    5: ("┌─────────┐", 
        "│  •   •  │", 
        "│    •    │", 
        "│  •   •  │", 
        "└─────────┘"),
    6: ("┌─────────┐", 
        "│  •   •  │", 
        "│  •   •  │", 
        "│  •   •  │", 
        "└─────────┘")
}

# Function to print dice horizontally
def print_dice_horizontal(dice_faces):
    """
    Prints the ASCII representation of multiple dice side by side.
    :param dice_faces: List of dice face tuples.
    """
    for row in range(5):  # Each dice face has 5 rows
        print("  ".join(die[row] for die in dice_faces))  # Print corresponding rows from all dice
    print("")  # Print a blank line for spacing

# Function to print dice vertically
def print_dice_vertical(dice_faces):
    """
    Prints the ASCII representation of multiple dice stacked vertically.
    :param dice_faces: List of dice face tuples.
    """
    for die in dice_faces:
        for row in die:
            print(row)  # Print each row of the dice face
        print("")  # Space between dice

# Ask user how they want the dice to be printed
while True:
    orientation = input("Do you want to print the dice horizontally or vertically? (h/v): ").strip().lower()
    if orientation in ['h', 'v']:
        break
    print("Invalid input. Please enter 'h' for horizontal or 'v' for vertical.")

# Ask the user how many dice they want to roll
NO = int(input("How many dice do you want to roll? "))

total = 0  # Variable to store the sum of all rolled dice
rolled_dice = []  # List to store the dice faces rolled

# Roll the dice as many times as the user requested
for _ in range(NO):
    r = random.randint(1, 6)  # Generate a random number between 1 and 6
    rolled_dice.append(dice[r])  # Add the corresponding dice face to the list
    total += r  # Add the rolled number to the total sum

# Print the rolled dice faces based on user's choice
if orientation == 'h':
    print_dice_horizontal(rolled_dice)
else:
    print_dice_vertical(rolled_dice)

# Print the total value of all rolled dice
print(f"Your total is: {total}")
