import pandas as pd
import random
import numpy as np

def generate_dirty_dataset(output_path):
    order_id = list(range(1, 201))
    names = ["Alex", "Emma", "Jhon", "Patrick", "Gemma", "Chris", "Louise", "Charles", "Nicky", "Harry"]
    country = ["Spain", "France", "Germany", "Italy", "United Kingdom", "United States", "Canada", "Japan", "China", "Australia"]
    dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
    age = np.random.randint(1, 80, size=200).tolist()
    purchase_amount = np.round(np.random.uniform(10.0, 10000.0, size =200))
    purchase_date = np.random.choice(dates, size = 200)
    customer_name = np.random.choice(names, size = 200)
    customer_country = np.random.choice(country, size = 200)
    df = pd.DataFrame({"order_id": order_id, 
                       "age": age, 
                       "purchase_amount": purchase_amount,
                       "purchase_date":purchase_date,
                       "customer_name":customer_name,
                       "country":customer_country})
    
    
    df["purchase_amount"] = df["purchase_amount"].astype(object)
    df["purchase_date"] = (df["purchase_date"]).astype(object)
    
    indices = df.sample(frac= 0.1, random_state=42).index
    indices2 = df.sample(frac= 0.08, random_state=43).index
    indices3 = df.sample(frac= 0.15, random_state=44).index
    indices4 = df.sample(frac= 0.09, random_state=45).index
    indices5 = df.sample(frac= 0.07, random_state=46).index

    df.loc[indices, "age"] = np.nan
    df.loc[indices2, "purchase_amount"] = np.nan
    df.loc[indices3, "purchase_date"] = np.nan
    df.loc[indices4, "customer_name"] = np.nan
    df.loc[indices5, "country"] = np.nan
    
    outliers = [999, -3, 0, 150, 200]
    outliers2 = [999999.99, -500.0, -1.0, 888888.0, -999.0]
    invalid_data = ["N/A", "Unknown", "None", "Missing", "--", " ", "null", "NULL", "NaN", "nan"]
    invalid_dates = ["2024/13/01", "31-02-2024", "2024.01.01", "01-01-2024", "2024/01/32", "2024-00-10", "2024-12-32", "2024/00/15", "2024.13.01", "2024-01-00", "2024/01/00", "2024-01-32", "2024.01.32", "2024/13/01", "2024-00-10"]
    indices6 = df.sample(5, random_state=47).index
    indices7 = df.sample(5, random_state=49).index
    indices8 = df.sample(10, random_state=50).index
    indices9 = df.sample(15, random_state=51).index
    
    df.loc[indices6, "age"] = outliers
    df.loc[indices7, "purchase_amount"] = outliers2
    df.loc[indices8, "purchase_amount"] = invalid_data
    df.loc[indices9, "purchase_date"] = invalid_dates
    
    print(df.info())
    print(df.loc[indices6, "age"])
    print(df.loc[indices7, "purchase_amount"])
    print(df.loc[indices8, "purchase_amount"])
    print(df.loc[indices9, "purchase_date"])
    
    
    df.to_csv(output_path, index=False)

if __name__ == "__main__":
    generate_dirty_dataset("data/dirty_dataset.csv")