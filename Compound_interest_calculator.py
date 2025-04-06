# user input principal amount
p = int(input("Enter your principal value: "))

# user input the rate (as a percentage, needs to be converted to decimal)
r = float(input("Enter your rate (annual interest rate in %): ")) / 100

# user input number of times the interest is compounded per year
n = int(input("Enter number of times that interest is compounded per year: "))

# user input time
t = int(input("Enter the number of years the money is invested or borrowed for: "))

# calculate compound interest
a = p * (1 + r / n) ** (n * t)

# print the final amount
print(f"Your final amount is {a:.2f}")
