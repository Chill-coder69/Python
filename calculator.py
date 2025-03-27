operation=input("enter your operator : ")                      # choose the opeation(*,/,+,-)
if operation not in ["+","-","*","/"]:                        # detects any invalid input
    print("your operator in not valid")    
    exit()                                                       # exit on invalid input
first_no=int(input("enter first no. : "))                        # first number
sec_no=int(input("enter second no. : "))                         # second number
result= {"/": c/b ,'*':c*b , "+":c+b , "-" : c-b}                # results
print(f"{first_no} {operation} {sec_no} is {result[operation]}") # give output
