# user input principal amount
p =int(input("enter your principal value : "))

# user input the rate
r =int(input("enter your rate : "))

# user input no. of time the interest is compounded
n =int(input("enter number of times that interest is compounded per year : "))

# user input time
t = int(input("enter the number of years the money is invested or borrowed for : "))

# put each variable in formula and calculate
a = p*(1 + r/n)(n*t)

# print the final amount
print(f"your final amount is {a}")
