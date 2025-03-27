operation=input("enter your operator : ")
if operation not in ["+","-","*","/"]:
    print("your operator in not valid")    
    exit()    
first_no=int(input("enter first no. : "))
sec_no=int(input("enter second no. : "))
result= {"/": c/b ,'*':c*b , "+":c+b , "-" : c-b}
print(f"{first_no} {operation} {sec_no} is {result[operation]}")
