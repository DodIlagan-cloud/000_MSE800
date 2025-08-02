def factorial():
    number = input("input value(PLEASE PUT INTENGER NUMBER):")
    n = int(number)

    if n < 0:
        return "Unidentify number lower than zero"

    elif 0 <= n <= 1:
        return 1

    else:
        result = 1
        for i in range(1, n + 1):
            print(", ",i)    
            result *= i # result = result *i
        return result
        # i = 1
        # while i <= n:
        #     print(", ", i)
        #     result *= i
        #     i += 1
        # return result

if __name__ == "__main__":
    ans = factorial()
    print("\n Final result:", ans)