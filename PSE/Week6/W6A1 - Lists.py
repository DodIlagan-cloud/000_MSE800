## extract information with age greater than 25 from the following list of dictionaries
#data = [{"name": "Alice", "age": 28}, {"name": "Bob", "age": 24}, {"name": "Charlie", "age": 30}]
#
#for i in data: 
#    if i ['age'] > 25:
#        print(i)
#
#
## use list comprehension to flatten the matrix
#matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
#for i in matrix:
#    for j in i:
#        print(j, end=" ")




#Matrix2 = [[0, 2, -3], [4,5,6], [7,8,9]]
## Sum_matrix = matrix + Matrix2 ...??
## Mul_matrix = matrix * Mmatrix2 ...??
#for add1 in Matrix2:
#    for add2 in add1

data = []
for i in range(5):
    
    data.append(lambda a, i=i*2: i*a)
 
    print(data[i](1))
   print(a)
