# This program is a guessing game where players try to guess a randomly generated number
# The player who guesses the number in the least number of attempts wins
# If there is a tie, all players with the minimum number of attempts win

import random
a = random.randint(1,50)
e=input("no. of players: ")
d=[]
for i in range(int(e)):
    d.append(input(f"Enter your name player{i+1}: "))
count = 1

# Store results for each player
results = {}

# Play the game for each player
for i in d:
    print(f"player {i}'s turn")
    b=int(input("Enter your guess: "))
    attempts = 0
    
    while a != b:
        attempts += 1
        if a > b:
            print("too low")
        elif a < b:
            print("too high")
        b = int(input("Enter your guess: "))
    
    # Add one more for the correct guess
    attempts += 1
    print(f"{i} guessed correctly in {attempts} attempts")
    results[i] = attempts

# Find the winner (player with minimum attempts)
winner = min(results, key=results.get)
min_attempts = results[winner]

# Check if there's a tie
winners = [player for player, attempts in results.items() if attempts == min_attempts]

if len(winners) > 1:
    print(f"It's a tie between {', '.join(winners)} with {min_attempts} attempts each!")
else:
    print(f"The winner is {winner} with {min_attempts} attempts!")
