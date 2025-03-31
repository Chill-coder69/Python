p =int(input("enter your principal value : "))        # user input principal amount
r =int(input("enter your rate : "))                   # user input the rate
n =int(input("enter number of times that interest is compounded per year : "))  # user input no. of time the interest is compounded
t = int(input("enter the number of years the money is invested or borrowed for : "))  # user input time
a = p*(1 + r/n)(n*t)      # put each variable in formula and calculate
print(f"your final amount is {a}")  # print the final amount
