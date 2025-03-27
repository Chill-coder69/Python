Your_conversion=input("you want to convert pound to kg or kg to pound : ")
if Your_conversion=="pound to kg":
    your_weight_in_pound=int(input("enter weight in pound : "))
    print(f"the kg is :{your_weight_in_pound*0.453592} ")
elif Your_conversion=="kg to pound":
    your_weight_in_kg=int(input("enter weight in kg : "))
    print(f"the pound is :{your_weight_in_kg*2.20462}")
