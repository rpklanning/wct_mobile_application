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
    #TODO need to add description of function
    # call function to read the database data needed for the program

    logger.info("")
    logger.info("------------------------------------------------------------------------------------")
    logger.info("Module: misc_functions.py     Function: DATABASE_READ_AND_STREAMLIT_INPUT_GENERATION")
    logger.info("Read Databases and develop variables for Streamlit HMI")

    logger.info("Attempt to read Database: wct_unposted_ledger Table: unposted_ledger")
    st.session_state.df_unposted_ledger = READ_NEON_DB_TABLE_INTO_DATAFRAME("wct_unposted_ledger",
                                                                            "unposted_ledger")
    logger.info("Success - dataframe: st.session_state.df_unposted_ledger generated from database table.")

    logger.info("")
    logger.info("Attempt to read Database: wct_data Table: projects_list and get a list of active projects.")
    df_projects_list = READ_NEON_DB_TABLE_INTO_DATAFRAME("wct_data", "projects_list")
    logger.info("Success - dataframe: df_projects_list has been generated from database table")
    logger.info("Attempt to generate the active projects list")
    # call function to get list of active projects from dataframe: df_projects_list
    st.session_state.lst_active_projects = GET_ACTIVE_RECORDS_FROM_DATABASE(df_projects_list,
                                                                            "wct_data/projects_list",
                                                                            "Project", "Status")
    logger.info("Success - List of active projects has been generated.")
    logger.info(f"Active projects:{st.session_state.lst_active_projects}")

    logger.info("")
    logger.info("Attempt to read Database: wct_data Table: suppliers_list and get a list of active suppliers.")
    df_suppliers_list = READ_NEON_DB_TABLE_INTO_DATAFRAME("wct_data", "suppliers_list")
    logger.info("Success - dataframe: df_suppliers_list has been generated from data table.")
    # call function to get list of active suppliers from dataframe: df_suppliers_list
    st.session_state.lst_active_suppliers = GET_ACTIVE_RECORDS_FROM_DATABASE(df_suppliers_list,
                                                                             "wct_data/suppliers_list",
                                                                             "Company",
                                                                             "Status")
    logger.info("Success - List of active suppliers has been generated.")
    logger.info(f"Active suppliers:{st.session_state.lst_active_suppliers}")


    logger.info("")
    logger.info("Attempt to determine database key by reading dataframe: df_unposted_ledger, get the max value in the "
                "No column, and increment the value by 1")
    # call function to get the max value in field "No" in the dataframe: df_unposted_ledger and increment by 1
    st.session_state.next_id_no = GET_NEW_NO_COL_RECORD_VALUE(st.session_state.df_unposted_ledger)
    logger.info(f"Value for database key determined = {st.session_state.next_id_no}")

    # call function to get today's date
    st.session_state.todays_date = GET_TODAYS_DATE_AND_FORMAT()
    logger.info(f"Value for todays date: st.session_state.todays date has been determined: "
                f"{st.session_state.todays_date}")


@st.cache_data
def GET_NEW_NO_COL_RECORD_VALUE(df):
    """
    Function will receive the dataframe and read the No column into a list, if possible.  The No column is a key field
    so the values cannot be duplicated.  If no records exist in the database No column, then the first record will have
    a No value of 0.  If records exists, the list wil be created and converted to integers and so that the
    maximum value can be determined.  The next record No value will be determined by incrementing the maximum value by
    1.  This will be converted to a string and returned to the calling program.
    :param df: dataframe containing the No column
    :return: no_col_new_value - string of the incremented max value of the No column
    """

    logger.info("")
    msg = ("FUNCTION WILL PARSE THE DATABASE/TABLE: wct_unposted_ledger/unposted_ledger MAX COLUMN: No VALUE AND "
           "INCREMENT BY 1")
    logger.info(msg)
    logger.info("Attempt to convert 'No' column to list.")
    # read the "No" field of the dataframe into a list.
    try:
        lst_no_col_str = df['No'].tolist()
        msg = (f"Conversion of 'No' column to list was successful. The list contains the following: "
               f"{len(lst_no_col_str)} items.")
        logger.info(msg)
        logger.info(f"{lst_no_col_str}")

    except KeyError as e:
        logger.error(f"KeyError captured: The column {e} does not exist in the DataFrame.")
        lst_no_col_str = []
        no_col_next_value = "X"
        return no_col_next_value

    # check if there is any data in the database table.
    if len(lst_no_col_str) == 0:
        # if not, set the first id value in the table to 0
        no_col_next_value = "0"
    else:
        # convert the string values in No column to integers using list comprehension and get the max value
        lst_no_col_int = [int(x) for x in lst_no_col_str]
        no_col_max_value = max(lst_no_col_int)
        logger.info(f"No column has been converted to integers and the max value is: {no_col_max_value}")

        # increment the max value in No column of dataframe by 1 and convert to string
        no_col_next_value = str(no_col_max_value + 1)
        logger.info(f"No column has been incremented and the next id value is: {no_col_next_value}")

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


def CLEAR_CACHES_AND_CALL_UPDATE_DBASES():
    # TODO add description
    logger.info("------------------------------------------------------------------------------------")
    logger.info("Module: misc_functions.py     Function: CLEAR_CACHES_AND_CALL_UPDATE_DBASES")
    try:
        logger.info("")
        logger.info("Clear Caches and Call Update Database Function Actions")
        # delete the camera widgets key to close the camera.  When the program is rerun, it will reinitialize.
        if "my_camera_key" in st.session_state:
            del st.session_state["my_camera_key"]

        # reset screen to close the dataframe expander
        st.session_state.generate_new_dataframe = False

        logger.info("Call the functions to clear the streamlit caches.")
        # clear the caches which read the databases and set the default HMI values
        READ_NEON_DB_TABLE_INTO_DATAFRAME.clear()
        GET_NEW_NO_COL_RECORD_VALUE.clear()
        GET_ACTIVE_RECORDS_FROM_DATABASE.clear()
        GET_TODAYS_DATE_AND_FORMAT.clear()
        logger.info("Success - Caches have been cleared.")

        # call function to read the databases and update the hmi data
        DATABASE_READ_AND_STREAMLIT_INPUT_GENERATION()

        status = "True"
        return status
    except:

        status = "False"
        return status







