"""Week 3 - Activity 3 : Count the words in the file
Develop a Python project using an object-oriented (OO) approach to convert large datasets into Parquet format. 
Then, compute the maximum, minimum, average, and absolute values for each column in the dataset. 
(see link to download a big numerical data in csv format from link: https://archive.ics.uci.edu/datasets)
Finally, share the GitHub repository link along with a screenshot of the results.
W3A3_CovertToParquet.py - Week 3 Activity 3
Eduardo JR Ilagan
"""


"""Variables Table
Variable Name	Role	Type	Demographic	Description	Units	Missing Values
Gender	Feature	Categorical	Gender			no
Age	Feature	Continuous	Age			no
Height	Feature	Continuous				no
Weight	Feature	Continuous				no
family_history_with_overweight	Feature	Binary		Has a family member suffered or suffers from overweight?		no
FAVC	Feature	Binary		Do you eat high caloric food frequently?		no
FCVC	Feature	Integer		Do you usually eat vegetables in your meals?		no
NCP	Feature	Continuous		How many main meals do you have daily?		no
CAEC	Feature	Categorical		Do you eat any food between meals?		no
SMOKE	Feature	Binary		Do you smoke?		no
"""
import pandas as pd
import pyarrow.parquet as pq

class DataFrameConverter:
    def __init__(self):
        """
        Initializes the DataFrameConverter.
        """
        self.dataframe = None
        print("DataFrameConverter initialized. Ready for data operations.")

    def read_data(self, input_file_path):
        try:
            self.dataframe = pd.read_csv(input_file_path)   
            print("Data loaded successfully into DataFrame.")
            print(f"DataFrame shape: {self.dataframe.shape}")
            print("First 5 rows:\n", self.dataframe.head())
            return self.dataframe
        except Exception as e:
            print(f"Error reading data: {e}")
            self.dataframe = None # Reset dataframe if reading fails
            return None
        
    def convert_to_parquet(self,output_parquet_file):
        try:
            # Use engine='pyarrow' for robust Parquet writing.
            # For large datasets, consider compression (e.g., compression='snappy', 'gzip', 'brotli')
            self.dataframe.to_parquet(output_parquet_file, engine='pyarrow', index=False)
            print("Conversion to Parquet successful!")
            return True
        except Exception as e:
            print(f"Error during Parquet conversion: {e}")
            return False



def main():
    input_csv_file = "ObesityDataSet.csv"
    output_parquet_file = "ObesityDataSet.parquet"
    input_file_path = r"G:\My Drive\00_Pers\000_MSE800\PSE\Week3\ObesityDataSet.csv"
    output_parquet_file= r"G:\My Drive\00_Pers\000_MSE800\PSE\Week3\ObesityDataSet.parquet"
    csvtoparquet = DataFrameConverter()
    panda_var = csvtoparquet.read_data(input_file_path)
    
    if panda_var is not None:
        conversion_success = csvtoparquet.convert_to_parquet(output_parquet_file)
        if conversion_success:
            print(f"\nSuccessfully converted '{input_csv_file}' to '{output_parquet_file}'.")
            # Optional: Verify the Parquet file
            print("\n--- Verifying Parquet File ---")
            try:
                parquet_data = pd.read_parquet(output_parquet_file, engine='pyarrow')
                print(f"Parquet file loaded successfully. Shape: {parquet_data.shape}")
                #print("First 5 rows from Parquet:\n", paraquet_data.head())
                max_age = parquet_data['Age'].max()
                min_ht = parquet_data['Height'].min()
                avg_wt = round(parquet_data['Weight'].mean(),2)
                #abs_val = parquet_data['Weight'].max().abs()
                match_rec = parquet_data[parquet_data['SMOKE'] == "yes"]
                count_rec = len(match_rec)
                print("Highest Age for participants of the study is: ", max_age)
                print("Lowest Height of a participant that joined the study is: ", min_ht)
                print("Average Weight of a participant that joined the study is: ", avg_wt)
                print("No Absolute Value for any of the columns. ")
                print("Number of people who are Smokers: ", count_rec)

                #max_age_mae = 

            except Exception as e:
                print(f"Error verifying Parquet file: {e}")
        else:
            print(f"\nFailed to convert '{input_file_path}' to Parquet.")
    else:
        print("\nSkipping Parquet conversion due to data reading failure.")
if __name__ == "__main__":
    main()