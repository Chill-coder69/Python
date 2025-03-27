Your_conversion=input("you want to convert pound to kg or kg to pound : ") # enter your weight here
if Your_conversion=="pound to kg":                                         # check if convertion in pound to kg
    your_weight_in_pound=int(input("enter weight in pound : "))
    print(f"the kg is :{your_weight_in_pound*0.453592} ")                  # give output in kg
elif Your_conversion=="kg to pound":                                       # check if convertion in kg to pound
    your_weight_in_kg=int(input("enter weight in kg : "))
    print(f"the pound is :{your_weight_in_kg*2.20462}")                    # give output in pounds
else:
    print(f"")
