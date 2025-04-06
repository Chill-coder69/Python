# Ask user for conversion type
Your_conversion = input("Do you want to convert 'pound to kg' or 'kg to pound'? ").strip().lower()

# Convert pound to kg
if Your_conversion == "pound to kg":
    your_weight_in_pound = float(input("Enter weight in pounds: "))
    print(f"The weight in kg is: {your_weight_in_pound * 0.453592:.2f}")

# Convert kg to pound
elif Your_conversion == "kg to pound":
    your_weight_in_kg = float(input("Enter weight in kg: "))
    print(f"The weight in pounds is: {your_weight_in_kg * 2.20462:.2f}")

# Handle invalid input
else:
    print("Invalid input. Please choose either 'pound to kg' or 'kg to pound'.")
