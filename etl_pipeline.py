import pandas as pd
from sqlalchemy import create_engine

# Initialize SQLite Database Engine
engine = create_engine('sqlite:///university_dw.db')

def fetch_and_transform_data():
    print("Fetching REAL publicly available datasets...")
    
    # 1. Placement & Student Performance Data
    url_placement = "https://raw.githubusercontent.com/ShuklaPrashant21/Campus_Recruitment/master/Placement_Data_Full_Class.csv"
    df_placement = pd.read_csv(url_placement)
    
    # Transform Placement Data
    df_placement = df_placement[['sl_no', 'gender', 'degree_t', 'degree_p', 'specialisation', 'status', 'salary']].copy()
    df_placement['salary'] = df_placement['salary'].fillna(0) # Unplaced students have 0 salary
    df_placement.rename(columns={'sl_no': 'Student_ID', 'degree_p': 'CGPA_Percentage', 'degree_t': 'Department', 'status': 'Placement_Status'}, inplace=True)
    
    # 2. Student Attendance Data 
    url_attendance = "https://raw.githubusercontent.com/guipsamora/pandas_exercises/master/04_Apply/Students_Alcohol_Consumption/student-mat.csv"
    df_att = pd.read_csv(url_attendance)
    
    # Transform Attendance Data
    df_att = df_att[['sex', 'age', 'studytime', 'failures', 'absences', 'G3']].copy()
    df_att['Student_ID'] = range(1, len(df_att) + 1)
    df_att['Attendance_Percentage'] = ((93 - df_att['absences']) / 93) * 100
    df_att['Attendance_Percentage'] = df_att['Attendance_Percentage'].clip(upper=100)
    
    # 3. Faculty Workload Data 
    url_faculty = "https://raw.githubusercontent.com/manuclaeys/esiea_modeles_pour_la_data_science_2018_2020/master/Salaries.csv"
    df_faculty_raw = pd.read_csv(url_faculty)
    
    # FIX: Using strict positional indexing (.iloc) to avoid Pandas string-matching KeyError
    df_faculty = pd.DataFrame()
    df_faculty['Faculty_ID'] = df_faculty_raw.iloc[:, 0]
    df_faculty['Designation'] = df_faculty_raw.iloc[:, 1]
    df_faculty['Department'] = df_faculty_raw.iloc[:, 2]
    df_faculty['Years_Experience'] = df_faculty_raw.iloc[:, 3]
    df_faculty['Years_Service'] = df_faculty_raw.iloc[:, 4]
    
    # Derive a workload metric based on years of service (base 40 hours - reduction for seniority)
    df_faculty['Weekly_Workload_Hours'] = 40 - (df_faculty['Years_Service'] * 0.2)
    df_faculty['Weekly_Workload_Hours'] = df_faculty['Weekly_Workload_Hours'].clip(lower=15)
    
    return df_placement, df_att, df_faculty

def load_to_db(df_placement, df_att, df_faculty):
    print("Loading datasets into the Data Warehouse (SQLite)...")
    df_placement.to_sql('Fact_Placement', con=engine, if_exists='replace', index=False)
    df_att.to_sql('Fact_Attendance', con=engine, if_exists='replace', index=False)
    df_faculty.to_sql('Fact_Faculty', con=engine, if_exists='replace', index=False)
    print("ETL Pipeline completed successfully! Database ready.")

if __name__ == "__main__":
    placement, attendance, faculty = fetch_and_transform_data()
    load_to_db(placement, attendance, faculty)