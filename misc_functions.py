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
    '''
    Function will call functions to do the following:

    1. Read the Neon database: wct_unposted_ledger, table: unposted_ledger and store in a dataframe.
    2. Read the Neon database: wct_data, table: projects_list and get a list of active projects.
    3. Read the Neon database: wct_data, table: suppliers_list and get a list of active suppliers.
    4. Get the Neon database id key by determing the existing max value in the No column of dataframe: unposted_ledger.
    Increment the max value by 1.
    5. Get todays date and format per the project requirement YYYYMMDD.

    The returned information will be stored in st.session.state variables.
    :return: None
    '''

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
    Function will receive the dataframe and read the No column into a list, if possible.  The No column is database
    key field so the values cannot be duplicated.  If no records exist in the database No column, then the next_id will
    have a value 0.  If records exists, a list of all data in the No column will be created.  All items in the list will
    be converted into integers.  The next_id value will be determined based on the maximum value in the list and
    incremented by 1.  The next_id value will be converted to a string.  This value will be stored in a st.session_state
     variable.

    :param df: dataframe containing the No column
    :return: no_col_next_value - string containing the next id no. or "99999" which indicates an error.
    """

    logger.info("")
    logger.info("------------------------------------------------------------------------------------")
    logger.info("Module: misc_functions.py     Function: GET_NEW_NO_COL_RECORD_VALUE")
    logger.info("")
    msg = ("FUNCTION WILL PARSE THE DATABASE/TABLE: wct_unposted_ledger/unposted_ledger MAX COLUMN: No VALUE AND "
           "INCREMENT BY 1")
    logger.info(msg)
    logger.info("Attempt to convert 'No' column of dataframe into a list.")
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
        no_col_next_value = "99999"
        return no_col_next_value

    # check if there is any data in the database table.
    if len(lst_no_col_str) == 0:
        # if not, set the first id value in the table to 0
        no_col_next_value = "0"
    else:
        # convert the string values in No column to integers using list comprehension and get the max value
        lst_no_col_int = [int(x) for x in lst_no_col_str]
        no_col_max_value = max(lst_no_col_int)
        logger.info(f"No column of dataframe has been converted to integers and the max value is: {no_col_max_value}")

        # increment the max value in No column of dataframe by 1 and convert to string
        no_col_next_value = str(no_col_max_value + 1)
        logger.info(f"No column has been incremented and the next id value is: {no_col_next_value}")

        if no_col_next_value is not "":
            logger.info("Success - Obtained 'No' column max value, incremented by 1, and converted value: "
                        "{no_col_next_value} to string.")

    return no_col_next_value


@st.cache_data
def GET_ACTIVE_RECORDS_FROM_DATABASE(df, dbase, get_column, status_column):
    """
    Function will parse a dataframe, which is derived from a database, and return a list of values in a column
    (get_column) based on the value of another column (status_column) being "Active"
    :param df: dataframe containing the data to be obtained
    :param get_column: column name to be returned from the dataframe based on the status_column
    :param status_column: column name which will be evaluated to confirm it is "Active"
    :return: active_list - list of get_column values or empty on Error
    """

    logger.info("")
    logger.info("------------------------------------------------------------------------------------")
    logger.info("Module: misc_functions.py     Function: GET_ACTIVE_RECORDS_FROM_DATABASE")
    logger.info("Starting function to get Active Records from the dataframe, which is derived from a database")
    msg = (
        f"FUNCTION WILL PARSE A DATAFRAME, WHICH IS DERIVED FROM DATABASE/TABLE: {dbase}, TO OBTAIN A LIST OF VALUES "
        f"FROM A SPECIFIC COLUMN: {get_column} BASED ON THE VALUE IN COLUMN: {status_column} BEING 'Active'.")
    logger.info(msg)
    # parse the database
    try:
        # parse the df to develop an active list
        msg = (f"Attempt to get list of records in dataframe column: {get_column} based on value in column:"
               f" {status_column} being 'Active'.")
        logger.info(msg)
        active_list = df.loc[df['Status'] == "Active", get_column].tolist()
        logger.info("Success - Generating active column: {get_column}.")
        logger.info(f"Active columns: {active_list}")
        return active_list

    except KeyError as e:
        logger.error(f"Error - KeyError captured: Column {e} does not exist in the dataFrame.")
        active_list = []
        logger.info(f"Active columns: {active_list}")
        return active_list


@st.cache_data
def GET_TODAYS_DATE_AND_FORMAT():
    """
    Function will get todays date and format in YYYYMMDD format.
    :return: day_str - string containing todays date
    """

    logger.info("")
    logger.info("------------------------------------------------------------------------------------")
    logger.info("Module: misc_functions.py     Function: GET_TODAYS_DATE_AND_FORMAT")
    logger.info("")
    logger.info("Starting function to get todays date.")

    # generate and display today's data
    day = date.today()
    day_str = (str(day)).replace("-", "")
    logger.info(f"Success - Obtained todays date: {day_str}")
    return day_str


def CLEAR_CACHES_AND_CALL_UPDATE_DBASES():
    """
    Function will do the following:
    1. Clear the streamlit caches.  The caches to be cleared are:
        READ_NEON_DB_TABLE_INTO_DATAFRAME - allows rereading of the databases
        GET_NEW_NO_COL_RECORD_VALUE.clear() - allows getting the next value from the database
        GET_ACTIVE_RECORDS_FROM_DATABASE.clear() - allows getting the active records from the databases
        GET_TODAYS_DATE_AND_FORMAT.clear() - allows getting todays date

        Caches are used so that streamlit does not read the databases every cycle only on explicit direction

    2. Call the function: DATABASE_READ_AND_STREAMLIT_INPUT_GENERATION.  This function will update the data by
        sequentially reading all the databases and list, values, etc. used by the streamlit widgets.

    :return: None
    """
    logger.info("------------------------------------------------------------------------------------")
    logger.info("Module: misc_functions.py     Function: CLEAR_CACHES_AND_CALL_UPDATE_DBASES")
    try:
        logger.info("Starting function to Clear Caches and Call Update Database Function Actions")
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
