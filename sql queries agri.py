import streamlit as st
import mysql.connector
import pandas as pd

# Database Connection
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="12345678",
    database="agri_explorer"
)
mycursor = mydb.cursor()

# Streamlit App
st.title("Agriculture Data Analysis Dashboard")

# Define a function to execute queries and return results as DataFrame
def execute_query(query):
    mycursor.execute(query)
    data = mycursor.fetchall()
    if not data:
        return pd.DataFrame()
    columns = [desc[0] for desc in mycursor.description]
    return pd.DataFrame(data, columns=columns)

# Sidebar menu for selecting analysis
option = st.sidebar.selectbox("Select Analysis", [
    "Top 3 Rice Producing States by Year",
    "Top 5 Wheat Producing States (Last 5 Years)",
    "Top 5 States with Highest Oilseeds Growth Rate",
    "District-wise Correlation Between Area and Production",
    "Yearly Cotton Production for Top 5 States",
    "Top 5 Groundnut Producing Districts (2020)",
    "Average Maize Yield Over the Years",
    "Total Oilseeds Area by State",
    "Top 5 Districts with Highest Rice Yield",
    "Wheat vs Rice Production (Top 5 States, Last 10 Years)"
])

if option == "Top 3 Rice Producing States by Year":
    query = """
        SELECT year, state_name, SUM(rice_production) AS total_production
        FROM Rice_data
        GROUP BY year, state_name
        ORDER BY year, total_production DESC
        LIMIT 3;
    """
    st.dataframe(execute_query(query))

elif option == "Top 5 Wheat Producing States (Last 5 Years)":
    query = """
        SELECT wheat_data.state_name, SUM(wheat_data.wheat_area) AS total_area, 
               SUM(wheat_data.wheat_yield) AS total_yield
        FROM wheat_data
        WHERE wheat_data.year IN (
            SELECT year FROM (SELECT DISTINCT year FROM wheat_data ORDER BY year DESC LIMIT 5) AS subquery
        )
        GROUP BY wheat_data.state_name
        ORDER BY total_yield DESC
        LIMIT 5;
    """
    st.dataframe(execute_query(query))

elif option == "Top 5 States with Highest Oilseeds Growth Rate":
    query = """
        SELECT state_name, ((MAX(oilseeds_production) - MIN(oilseeds_production)) / MIN(oilseeds_production)) * 100 AS growth_rate
        FROM Other_Crops_data
        WHERE year BETWEEN (SELECT MAX(year) - 4 FROM Other_Crops_data) AND (SELECT MAX(year) FROM Other_Crops_data)
        GROUP BY state_name
        ORDER BY growth_rate DESC
        LIMIT 5;
    """
    st.dataframe(execute_query(query))

elif option == "District-wise Correlation Between Area and Production":
    query = """
        SELECT r.dist_name, ROUND(SUM(r.rice_area), 2) AS total_area_rice,
               ROUND(SUM(r.rice_production), 2) AS total_production_rice,
               ROUND(SUM(w.wheat_area), 2) AS total_area_wheat,
               ROUND(SUM(w.wheat_production), 2) AS total_production_wheat,
               ROUND(SUM(o.maize_area), 2) AS total_area_maize,
               ROUND(SUM(o.maize_production), 2) AS total_production_maize
        FROM Rice_data r
        JOIN Wheat_data w ON r.dist_code = w.dist_code AND r.year = w.year
        JOIN Other_Crops_data o ON r.dist_code = o.dist_code AND r.year = o.year
        GROUP BY r.dist_name;
    """
    st.dataframe(execute_query(query))

elif option == "Yearly Cotton Production for Top 5 States":
    query = """
        WITH top_states AS (
            SELECT state_name FROM Other_Crops_data
            GROUP BY state_name
            ORDER BY SUM(cotton_production) DESC
            LIMIT 5
        )
        SELECT year, state_name, SUM(cotton_production) AS total_production
        FROM Other_Crops_data
        WHERE state_name IN (SELECT state_name FROM top_states)
        GROUP BY year, state_name
        ORDER BY year, total_production DESC;
    """
    st.dataframe(execute_query(query))

elif option == "Top 5 Groundnut Producing Districts (2020)":
    query = """
        SELECT dist_name, state_name, groundnut_production
        FROM Other_Crops_data
        WHERE year = 2020
        ORDER BY groundnut_production DESC
        LIMIT 5;
    """
    st.dataframe(execute_query(query))

elif option == "Average Maize Yield Over the Years":
    query = """
        SELECT year, AVG(maize_yield) AS avg_maize_yield
        FROM Other_Crops_data
        GROUP BY year
        ORDER BY year;
    """
    st.dataframe(execute_query(query))

elif option == "Total Oilseeds Area by State":
    query = """
        SELECT state_name, SUM(oilseeds_area) AS total_oilseeds_area
        FROM Other_Crops_data
        GROUP BY state_name
        ORDER BY total_oilseeds_area DESC;
    """
    st.dataframe(execute_query(query))

elif option == "Top 5 Districts with Highest Rice Yield":
    query = """
        SELECT dist_name, state_name, MAX(rice_yield) AS max_rice_yield
        FROM Rice_data
        GROUP BY dist_name, state_name
        ORDER BY max_rice_yield DESC
        LIMIT 5;
    """
    st.dataframe(execute_query(query))

elif option == "Wheat vs Rice Production (Top 5 States, Last 10 Years)":
    query = """
        WITH top_states AS (
            SELECT state_name FROM (
                SELECT state_name, SUM(rice_production) + SUM(wheat_production) AS total_production
                FROM Rice_data
                INNER JOIN Wheat_data USING (state_name, year)
                WHERE year >= (SELECT MAX(year) - 9 FROM Rice_data)
                GROUP BY state_name
                ORDER BY total_production DESC
                LIMIT 5
            ) AS ranked_states
        )
        SELECT w.year, w.state_name, SUM(w.rice_production) AS total_rice_production, SUM(w.wheat_production) AS total_wheat_production
        FROM (
            SELECT year, state_name, rice_production, 0 AS wheat_production FROM Rice_data
            WHERE state_name IN (SELECT state_name FROM top_states) AND year >= (SELECT MAX(year) - 9 FROM Rice_data)
            UNION ALL
            SELECT year, state_name, 0 AS rice_production, wheat_production FROM Wheat_data
            WHERE state_name IN (SELECT state_name FROM top_states) AND year >= (SELECT MAX(year) - 9 FROM Wheat_data)
        ) AS w
        GROUP BY w.year, w.state_name
        ORDER BY w.year, total_rice_production DESC, total_wheat_production DESC;
    """
    st.dataframe(execute_query(query))

# Close database connection
mycursor.close()
mydb.close()