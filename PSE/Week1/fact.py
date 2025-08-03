def factorial():
    number = input("input value(PLEASE PUT INTENGER NUMBER):")
    n = int(number)

    if n < 0:
        return "Unidentify number lower than zero"
    ## Start negative For Loop # inefficient
    #elif 0 == n:
    #    return 1
    #else:
    #    result = 1
    #    for i in range(1, n):
    #        print(", ",i,n,result)
    ## End 

    elif 0 <= n <= 1:
        return 1
    
    else:
        result = 1
        ### Start For Loop
        #for i in range(1, n + 1):
        #    result *= i # result = result *i
        #    print(", ",i,result)    
        #return result
        ### End For Loop
        ## Start While Loop
        i = 1
        while i <= n:
            result *= i
            i += 1
            print(", ",i,result)
        return result
        #End While Loop
if __name__ == "__main__":
    ans = factorial()
    print("\n Final result:", ans)