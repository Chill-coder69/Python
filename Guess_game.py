# This program is a guessing game where players try to guess a randomly generated number
# The player who guesses the number in the least number of attempts wins
# If there is a tie, all players with the minimum number of attempts win

import random

# Get number of players
num_players = int(input("No. of players: "))
player_names = []

# Get player names
for i in range(num_players):
    name = input(f"Enter your name, Player {i+1}: ")
    player_names.append(name)

# Dictionary to store each player's number of attempts
results = {}

# Let each player play the game
for player in player_names:
    print(f"\n{player}'s turn:")
    target = random.randint(1, 50)  # NEW random number per player
    guess = int(input("Enter your guess: "))
    attempts = 0

    # Loop until the player guesses correctly
    while guess != target:
        attempts += 1
        if guess < target:
            print("Too low!")
        else:
            print("Too high!")
        guess = int(input("Enter your guess: "))

    attempts += 1  # Count the correct guess
    print(f"{player} guessed the number in {attempts} attempts.")
    results[player] = attempts

# Find the minimum number of attempts
min_attempts = min(results.values())

# Find all winners who got it in the least attempts
winners = [name for name, attempts in results.items() if attempts == min_attempts]

# Display winner(s)
if len(winners) > 1:
    print(f"\nIt's a tie between {', '.join(winners)} with {min_attempts} attempts each!")
else:
    print(f"\nThe winner is {winners[0]} with {min_attempts} attempts!")
