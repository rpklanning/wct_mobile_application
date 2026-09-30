import os
import pandas as pd
import psycopg2
from psycopg2 import sql
from neon_db_manager import READ_NEON_DB_TABLE_INTO_DATAFRAME
import logging
import streamlit as st
import datetime
from datetime import date

# setup error logging capture
logger = logging.getLogger("neon_db_app")

def DATABASE_READ_AND_STREAMLIT_INPUT_GENERATION():
    # call function to read the database data needed for the program
    df_unposted_ledger = READ_NEON_DB_TABLE_INTO_DATAFRAME("wct_unposted_ledger", "unposted_ledger")
    df_projects_list = READ_NEON_DB_TABLE_INTO_DATAFRAME("wct_data", "projects_list")
    df_suppliers_list = READ_NEON_DB_TABLE_INTO_DATAFRAME("wct_data", "suppliers_list")

    # call function to get the max value in field "No" in the dataframe: df_unposted_ledger
    unposted_ledger_next_no_column_value = GET_NEW_NO_COL_RECORD_VALUE(df_unposted_ledger)

    # call function to get list of active projects from dataframe: df_projects_list
    lst_active_projects = GET_ACTIVE_RECORDS_FROM_DATABASE(df_projects_list, "wct_data/projects_list","Project", "Status")

    # call function to get list of active suppliers from dataframe: df_suppliers_list
    lst_active_suppliers = GET_ACTIVE_RECORDS_FROM_DATABASE(df_suppliers_list, "wct_data/suppliers_list","Company", "Status")

    # call function to get today's date
    todays_date = GET_TODAYS_DATE_AND_FORMAT()

    return {
        "df": df_unposted_ledger,
        "active projects": lst_active_projects,
        "active suppliers": lst_active_suppliers,
        "date":todays_date,
        "next id" :unposted_ledger_next_no_column_value
        }

@st.cache_data
def GET_NEW_NO_COL_RECORD_VALUE(df):
    """
    Function will receive the dataframe and read the No column into a list.  The list will be converted to integers and
    the maximum value determined.  The new value will be determined by incrementing the maximum value by 1.  This will
    be converted to a string and returned to the calling program
    :param df: dataframe containing the No column
    :return: no_col_new_value - string of the incremented max value of the No column
    """

    logger.info("")
    msg = ("FUNCTION WILL PARSE THE DATABASE/TABLE: wct_unposted_ledger/unposted_ledger MAX COLUMN: No VALUE AND INCREMENT BY 1")
    logger.info(msg)
    logger.info("Attempt to convert 'No' column to list.")
    # read the "No" field of the dataframe into a list.
    try:
        lst_no_col_str = df['No'].tolist()
        logger.info("Conversion of 'No' column to list was successful.")

    except KeyError as e:
        logger.error(f"KeyError captured: The column {e} does not exist in the DataFrame.")
        lst_no_col_str = []
        no_col_next_value = "X"
        return no_col_next_value

    # convert the string values in No column to integers using list comprehension
    lst_no_col_int = [int(x) for x in lst_no_col_str]

    # get the max value in No column
    no_col_max_value = max(lst_no_col_int)

    # increment the max value in No column of dataframe by 1 and convert to string
    no_col_next_value = str(no_col_max_value + 1)

    if no_col_next_value is not "":
        logger.info("Obtaining 'No' column max value, incrementing, and converting to string was successful.")

    return no_col_next_value
@st.cache_data
def GET_ACTIVE_RECORDS_FROM_DATABASE(df, dbase, get_column, status_column):
    """
    Function will parse a dataframe and return a list of get_column items based on whether the status_colum
     is "Active"
    :param df: dataframe containing the data to be obtained
    :param get_column: column name to be returned from the dataframe based on the status_column
    :param status_column: column name which will be evaluated to confirm it is "Active"
    :return: active_list - list of get column records
    """
    logger.info("")
    msg = (f"PARSE DATABASE/TABLE: {dbase} TO GET A LIST OF RECORDS FROM COLUMN: {get_column} BASED ON COLUMN: {status_column}"
           f" VALUE BEING 'Active'.")
    logger.info(msg)
    # parse the database
    try:
        active_list = df.loc[df['Status'] == "Active", get_column].tolist()
        logger.info("Generation of the active {get_column} list was successful.")
        return active_list

    except KeyError as e:
        logger.error(f"KeyError captured: The column {e} does not exist in the DataFrame.")
        active_list = []

        return active_list

@st.cache_data
def GET_TODAYS_DATE_AND_FORMAT():
    logger.info("")

    # generate and display today's data
    day = date.today()
    day_str = (str(day)).replace("-","")
    return day_str

def UPDATE_DATABASES_AND_REFRESH_PROGRAM_DISPLAY():
    # delete the camera widgets key to close the camera.  When the program is rerun, it will reinitialize.
    if "my_camera_key" in st.session_state:
        del st.session_state["my_camera_key"]

    # reset screen to close the expander
    st.session_state.generate_photo = False
    st.session_state.generate_new_dataframe = False

    # clear the caches which read the databases and set the default HMI values
    GET_NEW_NO_COL_RECORD_VALUE.clear()
    GET_ACTIVE_RECORDS_FROM_DATABASE.clear()
    GET_TODAYS_DATE_AND_FORMAT.clear()

    # call function to update the databases and the hmi data
    DATABASE_READ_AND_STREAMLIT_INPUT_GENERATION()


def DATABASE_READ_AND_STREAMLIT_INPUT_GENERATION():
    ##################################### READ DB AND GENERATION EVENT RUNNING #######################################
    # call function to read the database data needed for the program
    df_unposted_ledger = READ_NEON_DB_TABLE_INTO_DATAFRAME("wct_unposted_ledger", "unposted_ledger")
    df_projects_list = READ_NEON_DB_TABLE_INTO_DATAFRAME("wct_data", "projects_list")
    df_suppliers_list = READ_NEON_DB_TABLE_INTO_DATAFRAME("wct_data", "suppliers_list")

    # call function to get the max value in field "No" in the dataframe: df_unposted_ledger
    unposted_ledger_next_no_column_value = GET_NEW_NO_COL_RECORD_VALUE(df_unposted_ledger)

    # call function to get list of active projects from dataframe: df_projects_list
    lst_active_projects = GET_ACTIVE_RECORDS_FROM_DATABASE(df_projects_list, "wct_data/projects_list", "Project",
                                                           "Status")

    # call function to get list of active suppliers from dataframe: df_suppliers_list
    lst_active_suppliers = GET_ACTIVE_RECORDS_FROM_DATABASE(df_suppliers_list, "wct_data/suppliers_list", "Company",
                                                            "Status")

    # call function to get today's date
    todays_date = GET_TODAYS_DATE_AND_FORMAT()

    return {
        "df": df_unposted_ledger,
        "active projects": lst_active_projects,
        "active suppliers": lst_active_suppliers,
        "date": todays_date,
        "next id": unposted_ledger_next_no_column_value
    }






