def sumofeven():
    number = input("input value(PLEASE PUT INTENGER NUMBER):")
    n = int(number)

    if n < 0:
        return "Unidentify number lower than zero"

    #elif 0 <= n <= 1:
    #    return 1
    else:
        sumeven = 0 
        for i in range(1, n + 1):   
            if i % 2 == 0:
                sumeven = sumeven + i
                print("even ",i,n,sumeven) 
                result = sumeven
        return result
if __name__ == "__main__":
    ans = sumofeven()
    print("\n Final result:", ans)