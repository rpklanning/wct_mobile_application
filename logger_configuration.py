import sys
import io
import streamlit as st
from datetime import date, datetime
import logging

# setup error logging capture
logger = logging.getLogger("neon_db_app")

def LOGGER_CONFIGURATION():
    """
    Function will perform the following:
    1. establish the unique filename of the Error Log
    2. assign the session_state variable
    3. configure thelogger
    4. configure the file handler for display of the error log file in the streamlit application
    5. configure the stream handler for storing the data in memory.
    :return: logger - logging object
    """
    # generate the error log filename
    # -----------------------------------------------------------------------------
    # Create the unique error log filename ONLY ONCE per Streamlit session
    # -----------------------------------------------------------------------------
    if "log_filename" not in st.session_state:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.log_filename = ( f"Error_Log_{timestamp}.log" )

    # -------------------------------------------------------------------------------
    # Create an in-memory log stream only once
    # -------------------------------------------------------------------------------
    if "log_stream" not in st.session_state:
        st.session_state.log_stream = io.StringIO()

    # -----------------------------------------------------------
    # Create a unique logger name for this session
    # -----------------------------------------------------------
    if "logger_name" not in st.session_state:
        st.session_state.logger_name = f"neon_db_app_{st.session_state.log_filename}"

    # ---------------------------------------------------------
    # Configure this sessions logger's only once
    # ---------------------------------------------------------
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        logger.propagate = False

        # # file handler
        # file_handler = logging.FileHandler(
        #     st.session_state.log_filename,
        #     mode="a",
        #     encoding="utf-8"
        # )
        # In-memory Streamlit handler
        stream_handler = logging.StreamHandler(
            st.session_state.log_stream
        )

        formatter = logging.Formatter( "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                                       datefmt="%Y-%m-%d %H:%M:%S"
                                       )

        #file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        #logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger

