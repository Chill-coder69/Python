# choose the opeation(*,/,+,-)
operation=input("enter your operator : ")

# detects any invalid input
if operation not in ["+","-","*","/"]:
    print("your operator in not valid")    
    # exit on invalid input
    exit()

# first number
first_no=int(input("enter first no. : "))

# second number
sec_no=int(input("enter second no. : "))

# results
result= {"/": c/b ,'*':c*b , "+":c+b , "-" : c-b}

# give output
print(f"{first_no} {operation} {sec_no} is {result[operation]}")
