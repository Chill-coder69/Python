# enter your weight here
Your_conversion=input("you want to convert pound to kg or kg to pound : ")

# check if convertion in pound to kg
if Your_conversion=="pound to kg":
    your_weight_in_pound=int(input("enter weight in pound : "))
# give output in kg
    print(f"the kg is :{your_weight_in_pound*0.453592} ")
    
# check if convertion in kg to pound
elif Your_conversion=="kg to pound":
    your_weight_in_kg=int(input("enter weight in kg : "))
    # give output in pounds
    print(f"the pound is :{your_weight_in_kg*2.20462}")
# detects any invalid output
else:
    print("Invalid input")
