import numpy as np

	## Convert the list to a NumPy array and print it.
	## Print the total rainfall for the week.
	## Print the average rainfall for the week.
	## Count how many days had no rain (0 mm).
    ## Print the days (by index) where the rainfall was more than 5 mm.

def store_data():
    rainfall_list = np.array([0.0, 5.2, 3.1, 0.0, 12.4, 0.0, 7.5])
    return rainfall_list


if __name__ == "__main__":
    rainfall_list = store_data()
    sumrf = np.round(np.sum(rainfall_list),2)
    averf = np.round(np.mean(rainfall_list),2)
    day0arr = np.where(rainfall_list == 0)[0]
    day0 = day0arr.size
    daya5 = np.where(rainfall_list > 5)[0]
    dayname = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] 
    #for index in daya5:
    #    print("this",index)
    #    print(f'\t ({daya5[index]} mm)')
    #    print(f'\t{dayname[index]} ({daya5[index]} mm)')
    daya5 = [daymap for daymap, rain_amt in zip(dayname, rainfall_list) if rain_amt > 5] 

    print("RainFall for the week:",rainfall_list)
    print("Total Rainfall for the week:",sumrf," mm")
    print("Average Rainfall for the week",averf," mm")
    print("Number of days that has no rain:",day0," days")
    print("Number of days that has rainfall more than 5:",daya5)

