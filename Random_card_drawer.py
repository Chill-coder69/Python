import random

# Define card suits and ranks
suits = ['♠', '♥', '♦', '♣']
ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

# Generate a full deck of cards
deck = [f"{rank}{suit}" for suit in suits for rank in ranks]

# Function to create ASCII art for a card
def create_card_art(card):
    rank = card[:-1]
    suit = card[-1]
    # Handle spacing for single vs double digit ranks
    left = rank if len(rank) == 2 else rank + " "
    right = rank if len(rank) == 2 else " " + rank
    return (
        "┌─────────┐",
        f"│{left}       │",
        f"│    {suit}    │",
        f"│       {right}│",
        "└─────────┘"
    )

# Function to print cards horizontally
def print_cards_horizontal(cards):
    for row in range(5):
        print("  ".join(card[row] for card in cards))
    print()

# Function to print cards vertically
def print_cards_vertical(cards):
    for card in cards:
        for row in card:
            print(row)
        print()

# Ask orientation
while True:
    orientation = input("Do you want to display the cards horizontally or vertically? (h/v): ").strip().lower()
    if orientation in ['h', 'v']:
        break
    print("Invalid input. Please enter 'h' or 'v'.")

# Ask how many cards to draw
while True:
    try:
        num = int(input("How many cards would you like to draw? (1-52): "))
        if 1 <= num <= 52:
            break
        else:
            print("Please enter a number between 1 and 52.")
    except ValueError:
        print("Please enter a valid number.")

# Shuffle and draw cards
random.shuffle(deck)
drawn = deck[:num]
ascii_cards = [create_card_art(card) for card in drawn]

# Print the cards
if orientation == 'h':
    print_cards_horizontal(ascii_cards)
else:
    print_cards_vertical(ascii_cards)

# Show the drawn cards as text too
print("You drew:", ", ".join(drawn))
