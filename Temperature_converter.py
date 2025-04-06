# Save user choice of conversion
User_input = input("What unit do you want to convert into what unit (e.g., 'C to F'): ").upper()

# Detect any invalid input
if User_input not in ["C TO F", "C TO K", "F TO C", "F TO K", "K TO C", "K TO F"]:
    print("The unit is invalid")
    exit()

# Take user temperature
User_temp = float(input(f"Type your temp in {User_input.split(' ')[0]}: "))

# Results dictionary
results = {
    "C TO F": (User_temp * 9/5) + 32,
    "C TO K": User_temp + 273.15,
    "F TO C": (User_temp - 32) * 5/9,
    "F TO K": ((User_temp - 32) * 5/9) + 273.15,
    "K TO C": User_temp - 273.15,
    "K TO F": ((User_temp - 273.15) * 9/5) + 32
}

# Give output
print(f"Your temperature in {User_input.split(' ')[2]}: {results[User_input]:.2f}")
