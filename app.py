import streamlit as st
import pandas as pd
import sqlite3
import os
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Set Page Config
st.set_page_config(page_title="University Analytics Platform", layout="wide")
st.title("🎓 Educational Data Warehouse Dashboard")
st.caption("Live OLAP Dashboard powered by public Kaggle and UCI datasets.")

# Load Data from Database
@st.cache_data
def load_data():
    conn = sqlite3.connect('university_dw.db')
    df_placement = pd.read_sql_query("SELECT * FROM Fact_Placement", conn)
    df_attendance = pd.read_sql_query("SELECT * FROM Fact_Attendance", conn)
    df_faculty = pd.read_sql_query("SELECT * FROM Fact_Faculty", conn)
    conn.close()
    return df_placement, df_attendance, df_faculty

df_placement, df_attendance, df_faculty = load_data()

# Create distinct tabs covering the 4 required scopes
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Student Performance", "Attendance", "Placement Statistics", "Faculty Workload", "🤖 AI Data Assistant"
])

with tab1:
    st.header("Student Performance Metrics")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Average Degree Percentage by Department")
        avg_cgpa = df_placement.groupby('Department')['CGPA_Percentage'].mean().reset_index()
        st.bar_chart(avg_cgpa.set_index('Department'))
    with col2:
        st.subheader("Distribution of Final Grades (G3)")
        grades = df_attendance['G3'].value_counts().sort_index()
        st.bar_chart(grades)

with tab2:
    st.header("Attendance Analytics")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Attendance Percentage Distribution")
        st.bar_chart(df_attendance['Attendance_Percentage'])
    with col2:
        st.subheader("Critical Attendance Alerts (< 75%)")
        low_att = df_attendance[df_attendance['Attendance_Percentage'] < 75]
        st.dataframe(low_att[['Student_ID', 'absences', 'Attendance_Percentage']], use_container_width=True)

with tab3:
    st.header("Placement Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Placement Status")
        placement_counts = df_placement['Placement_Status'].value_counts()
        st.bar_chart(placement_counts)
    with col2:
        st.subheader("Average Salary by Specialisation (INR)")
        placed_students = df_placement[df_placement['Placement_Status'] == 'Placed']
        avg_salary = placed_students.groupby('specialisation')['salary'].mean().reset_index()
        st.bar_chart(avg_salary.set_index('specialisation'))

with tab4:
    st.header("Faculty Workload Analysis")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Average Weekly Workload by Designation")
        workload = df_faculty.groupby('Designation')['Weekly_Workload_Hours'].mean().reset_index()
        st.bar_chart(workload.set_index('Designation'))
    with col2:
        st.subheader("Faculty Department Allocation")
        dept_counts = df_faculty['Department'].value_counts()
        st.bar_chart(dept_counts)

with tab5:
    st.header("Ask the AI about the University Data")
    st.caption("Powered by LangChain and Generative AI")
    
    # 1. We completely removed the st.text_input for the API Key here!
    
    user_question = st.text_input("Ask a question in plain English (e.g., 'Which student ID got placed with the highest package?')")
    
    # 2. We removed the api_key check from this button condition
    if st.button("Generate Answer") and user_question:
        with st.spinner("AI is analyzing the Data Warehouse..."):
            try:
                # 3. Your key stays hidden in the backend here
                os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY_HERE"
                
                db = SQLDatabase.from_uri("sqlite:///university_dw.db") 
                
                llm = ChatOpenAI(
                    temperature=0, 
                    model_name="llama-3.1-8b-instant", 
                    base_url="https://api.groq.com/openai/v1" 
                )
                
                db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True, return_direct=True)
                raw_result = db_chain.run(user_question)
                
                prompt = f"""
                The user asked this question: '{user_question}'
                The database returned this raw data: {raw_result}
                
                Write a single, friendly, natural sentence answering the user's question using the data provided. 
                Do not explain the SQL or the raw data format. Just answer the question directly like a helpful assistant.
                """
                
                friendly_response = llm.invoke([HumanMessage(content=prompt)])
                
                st.success(friendly_response.content)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")