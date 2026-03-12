print("Hello World")
time=12

a=0
b=0
def add(x,y):
    return x+y
add(a,b)
print(add(5,6))
letters = ['a', 'b', 'c']

def print_letters(list,index):
        if (index == len(list)):
         return 
        print(list[index])
        print_letters(list,index+1)


print_letters(letters,0)