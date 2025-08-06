import numpy as np

def store_data():
    temp_list = np.array([18.5, 19, 20, 25.0, 2, 30, 13.9])
    return temp_list

def ave_temp():
    ave_temp_val = np.round(np.mean(temp_list),2)
    return ave_temp_val

def hi():
    hi_temp = np.max(temp_list)
    return hi_temp

def lo():
    lo_temp = np.min(temp_list)
    return lo_temp

def convtoF():
    faren = temp_list * 9/5 + 32
    #print("Farenheit:",temp_list)
    return faren
def above20():
    a20=np.where(temp_list > 20)[0]
    return a20
#    for i 
if __name__ == "__main__":
    temp_list = store_data()
    arrsize = temp_list.size
    ave_temp_val = ave_temp()
    hi_temp = hi()
    lo_temp = lo()
    faren = convtoF()
    a20 = above20()
    print("Average Temp:",ave_temp_val)
    print("Highest Temp:",hi_temp, "Lowest Temp:",lo_temp)
    print("Farenheit:",faren)
    print("Temp that are above 20:",a20)
    #ans = factorial()
    #print("\n Final result:", ans)