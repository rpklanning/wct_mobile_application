import io
import time
import streamlit as st
from neon_db_manager import UPLOAD_DATAFRAME_TO_NEON_DATABASE
from logger_configuration import LOGGER_CONFIGURATION
from misc_functions import DATABASE_READ_AND_STREAMLIT_INPUT_GENERATION
from misc_functions import CLEAR_CACHES_AND_CALL_UPDATE_DBASES
from cloudinary_file_manager import UPLOAD_FILE_TO_CLOUDINARY
import pandas as pd
from dotenv import load_dotenv

#######################################################################
# PROGRAM CONFIGURATION PRIOR TO RUNNING MAIN SECTION CODE
#######################################################################
# Call function to initialize the error logger
logger = LOGGER_CONFIGURATION()
logger.info("===== LOGGER INITIALIZED =====")
logger.info(f'LOG FILE: {st.session_state.log_filename}')
logger.info(f"LOGGER NAME: {logger.name}")
logger.info(f"HANDLERS: {logger.handlers}")

# Load the .env file from the current directory
load_dotenv()

########################################################################
### DEFINE SESSION_STATE VARIABLES
########################################################################
if "document_id" in st.session_state:
    st.session_state.storage_id = ""

if "next_id_no" not in st.session_state:
    st.session_state.next_id_no = ""

if "amount_number" not in st.session_state:
    st.session_state.amount_number = 0.00

if "img_file_buffer" not in st.session_state:
    st.session_state.img_file_buffer = ""

if "captured_image" not in st.session_state:
    st.session_state.captured_image = None

if "generate_revised_dataframe" not in st.session_state:
    st.session_state.generate_revised_dataframe = False

if "toggle_upload_photo" not in st.session_state:
    st.session_state.toggle_upload_photo = True

if "toggle_upload_error_log" not in st.session_state:
    st.session_state.toggle_upload_error_log = False

# TODO btn_refresh not tied to anything
if "btn_refresh" not in st.session_state:
    st.session_state.btn_refresh = False

if "df_uposted_ledger" not in st.session_state:
    st.session_state.df_unposted_ledger = pd.DataFrame(columns=["Column1", "Columns"])

if "df_revised" not in st.session_state:
    st.session_state.df_revised = pd.DataFrame(columns=["Column1", "Columns"])

if "todays_date" not in st.session_state:
    st.session_state.todays_date = ""

#######################################################################
### FUNCTIONS CODE AREA
#######################################################################
def BTN_REFRESH_EVENT():
    """
    Event which is triggered when the Refresh button is pressed.
    :return:
    """
    logger.info("")
    logger.info("---------------------------------------------------------------------------")
    logger.info("Module: main.py    Function: BTN_REFRESH_EVENT")
    logger.info("### START EXECUTION OF BUTTON REFRESH EVENT")

    # call the function to read the database and update the streamlit inputs
    DATABASE_READ_AND_STREAMLIT_INPUT_GENERATION()

###################################################################
### MAIN STREAMLIT SECTION
###################################################################
def STREAMLIT_MAIN():
    logger.info("")
    logger.info("START OF STREAMLIT PROGRAM")
    logger.info("############################################################################")
    logger.info("Module: main.py     Function: ----")
    logger.info("Configure web page layout")
    # page configuration
    st.set_page_config(page_title="Web Cost Tracker Mobile Application", layout="wide")
    st.markdown('<p style="text-align: center; font-size: 24px;"><b>Web Cost Tracker Mobile Application<b></p>',
                unsafe_allow_html=True)
    # change the background color of the application
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background-color: #27EBF5;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    logger.info("Insert HMI labels")
    line_height = '3.7'
    col1, col2, col3, col4 = st.columns([2, 1, 1.5, 2])

    # ================================================================
    # DISPLAY THE LABELS IN COLUMN 1
    # ================================================================
    with col2:
        st.markdown(f"<div style='line-height: {line_height}; font-weight: bold;'>Item ID No:</div>",
                    unsafe_allow_html=True)

        st.markdown(
            f"<div style='line-height: {line_height}; font-weight: bold;'>Todays Date:</div>",
            unsafe_allow_html=True
        )

        st.markdown(
            f"<div style='line-height: {line_height}; font-weight: bold;'>Select Charge Type:</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='line-height: {line_height}; font-weight: bold;'>Select Active Project:</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='line-height: {line_height}; font-weight: bold;'>Select Active Supplier:</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='line-height: {line_height}; font-weight: bold;'>Enter Charge Amount:</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='line-height: {line_height}; font-weight: bold;'>Generated Storage ID:</div>",
            unsafe_allow_html=True
        )

    # ================================================================
    # DISPLAY THE INPUT WIDGETS IN COLUMN 2
    # ================================================================
    logger.info("Insert HMI input widgets")
    with ((col3)):
        st.write("")

        id_no_placeholder = st.empty()

        todays_date_placeholder = st.empty()

        unposted_item_types = ['Matl', 'Sub', 'Equip']
        selected_type = st.selectbox("Select the Unposted Item Type:",
                                     options=unposted_item_types,
                                     label_visibility="collapsed")

        selected_project = st.selectbox("Select the active project:",
                                        options=st.session_state.lst_active_projects,
                                        label_visibility="collapsed")

        selected_supplier = st.selectbox("Select the active supplier:",
                                         options=st.session_state.lst_active_suppliers,
                                         label_visibility="collapsed")

        amount_number_placeholder = st.empty()

        # generate the unique storage_id from the user inputs.  Add the jpg extension used by Chrome and Safari.
        if selected_supplier is not None and selected_project is not None:
            st.session_state["storage_id"] = (selected_project + "_" + st.session_state.todays_date + "_" +
                                              selected_supplier + "_" + selected_type + "_" +
                                              st.session_state.next_id_no + ".jpg")

        st.text_input("storage_id",
                      key="storage_id",
                      label_visibility="collapsed",
                      disabled=True)

    # ===========================================================================
    # DISPLAY THE WEB PAGE CONTROL PANEL AND STATUS BAR
    # ===========================================================================
    logger.info("Insert HMI control panel widgets")
    # display the control panel with buttons (refresh, save) and toggles (upload photo, upload error log)
    colA, colB, colC, colD, colE, colF = st.columns([3, 1, 1, 1, 1, 3])
    with colB:
        # save button configuration is below - it must be reset after evaluating amount, photo toggle and photo status
        save_button_placeholder = st.empty()
    with colC:
        st.button("🔄 New / Refresh",
                  on_click=BTN_REFRESH_EVENT,
                  use_container_width=True)
    with colD:
        st.toggle("Upload Photo File",
                  key="toggle_upload_photo")
    with colE:
        st.toggle("Upload Error File", key="toggle_upload_error_log")

    colR, colS, colT = st.columns([1, 4, 1])
    with (colS):
        # status message is below - it must be reset after evaluating amount, photo toggle and photo status
        status_message_placeholder = st.empty()

    # ============================================================
    # CAMERA CODE SECTION
    # ============================================================
    if st.session_state.toggle_upload_photo:
        logger.info("Camera enabled.")
        colX, colY, colZ = st.columns([1, 4, 1])
        with colY:
            # configure camera input buffer
            logger.info("Configure inlet file buffer to enable taking a photo.")
            img_file_buffer = st.camera_input("Take picture using buttons below:",
                                              key="my_camera_key",
                                              resolution="1080p",
                                              )

            if img_file_buffer is not None:
                logger.info("Photo taken - convert bytes to captured image.")

                # read the image file buffer as bytes data to be transferred to Cloudinary
                bytes_data = img_file_buffer.getvalue()

                # convert bytes data into a file like object for the SDK
                st.session_state.captured_image = io.BytesIO(bytes_data)
                # get and display the file size
                bytes_len = len(img_file_buffer.getvalue())
                logger.info(f"Image has been taken and contains: {bytes_len} bytes.")

            else:
                # Camera image was cleared
                logger.info("Photo has been cleared or not taken.")
                st.session_state.captured_image = None

    # ============================================================
    # RENDER THE SAVE BUTTON PLACEHOLDER
    # ============================================================
    with save_button_placeholder:

        if st.button(
                "💾 Save Data / Files",
                key="save_button",
                use_container_width=True):

            # ====================================================================
            # BEGIN THE BUTTON SAVE EVENT
            # =====================================================================
            logger.info("")
            logger.info("------------------------------------------------------------------")
            logger.info("START EXECUTION OF BUTTON SAVE EVENT")

            # ================================================================
            # VALIDATE INPUTS
            # ================================================================

            amount_valid = st.session_state.amount_number != 0.00

            if st.session_state.toggle_upload_error_log:
                error_log_valid = st.session_state.log_filename is not None
            else:
                error_log_valid = True

            if st.session_state.toggle_upload_photo:
                photo_valid = (
                        st.session_state.captured_image is not None
                )
            else:
                photo_valid = True

            logger.info(f"amount_no: {st.session_state.amount_number}")
            logger.info(f"amount_valid: {amount_valid}")

            logger.info(f"photo_valid: {photo_valid}")
            logger.info(f"toggle_upload_photo: {st.session_state.toggle_upload_photo}")

            # ================================================================
            # INVALID INPUT
            # ================================================================

            if not amount_valid or not photo_valid:

                status_messages = []

                if not amount_valid:
                    status_messages.append(
                        "  Amount input is invalid!"
                    )

                if not photo_valid:
                    status_messages.append(
                        "  Photo image required!"
                    )

                if not error_log_valid:
                    status_messages.append(
                        "  Error log required!"
                    )

                status_msg = (
                        "❌ Input Status: "
                        + " ".join(status_messages)
                )

                # ============================================================
                # RENDER THE STATUS MESSAGE PLACEHOLDER
                # ============================================================
                with status_message_placeholder:
                    st.error(status_msg)

                logger.warning(status_msg)

            # ================================================================
            # VALID INPUT -- PERFORM SAVE
            # ================================================================

            else:
                # =============================================================================
                # RENDER THE STATUS MESSAGE PLACEHOLDER AND EXECUTE BUTTON SAVE EVENT
                # =============================================================================
                with status_message_placeholder:

                    with st.spinner("Saving data and files....", show_time=True):

                        try:
                            logger.info("")
                            logger.info("Upload Photo to Cloudinary")
                            logger.info(
                                "If toggle is true, call function to upload the photo to Cloudinary if image is NOT empty.")
                            logger.info(f"Toggle selection: {st.session_state.toggle_upload_photo}")

                            # ==================================================
                            # SAVE PHOTO FILE IF TOGGLE IS TRUE
                            # ==================================================
                            # call function to upload the photo to Cloudinary if image is not empty and toggle is True
                            if st.session_state.toggle_upload_photo:
                                # set storage type for a photo
                                storage_type = "photos"
                                # call function to upload the photo to Cloudinary
                                UPLOAD_FILE_TO_CLOUDINARY(st.session_state.captured_image,
                                                          st.session_state["storage_id"],
                                                          storage_type)

                            # ==================================================
                            # SAVE ERROR LOG FILE IF TOGGLE IS TRUE
                            # ==================================================
                            logger.info("")
                            logger.info("Upload Error Log to Cloudinary")

                            # convert the in-memory error log to a BytesIO object
                            log_contents = st.session_state.log_stream.getvalue()
                            log_file = io.BytesIO(log_contents.encode("utf-8"))
                            log_file.seek(0)

                            logger.info("If toggle is true, call function to upload the error log to Cloudinary.")
                            logger.info(f"Toggle selection: {st.session_state.toggle_upload_error_log}")
                            if st.session_state.toggle_upload_error_log:
                                # convert the in-memory error log to a BytesIO object = error_log_file
                                error_log_contents = st.session_state.log_stream.getvalue()
                                error_log_file = io.BytesIO(error_log_contents.encode("utf-8"))
                                error_log_file.seek(0)

                                # set storage type for an error log
                                storage_type = "error logs"

                                # call function to upload error log to cloudinary
                                log_upload_status = UPLOAD_FILE_TO_CLOUDINARY(error_log_file,
                                                                              st.session_state.log_filename,
                                                                              storage_type)

                            # ================================================================================
                            # REPLACE DATABASE: wct_uposted_ledger TABLE: unposted_ledger
                            # ================================================================================
                            logger.info("")
                            logger.info(f"Call function to upload new data to Neon database.")
                            # call function to upload the data into the database table
                            db_upload_status = UPLOAD_DATAFRAME_TO_NEON_DATABASE(st.session_state.df_revised,
                                                                                 "wct_unposted_ledger",
                                                                                 "unposted_ledger")
                            if not db_upload_status:
                                raise ValueError(
                                    " Error - File: Neon_db_manager, Function: UPLOAD_DATAFRAME_TO_NEON_DATABASE"
                                    "could not proceed.  Save event ended!"
                                )
                                return
                            else:
                                st.success("✅ Successfully updated the database and updated the program data.")
                                time.sleep(2)
                                status_message_placeholder.empty()

                            # continue executing save function by resetting streamlit widgets
                            # reset input variables
                            st.session_state.amount_number = 0.00
                            logger.info("Charge amount total on web page reset to $0.00.")

                            # disable the dataframe creation and expander section
                            st.session_state.generate_revised_dataframe = False

                            # update the status message
                            # status_msg = "❌ Input Status: Amount cannot be zero!"

                        except Exception as e:
                            st.error("❌ Error updating the database or saving files.  Retain receipts!")
                            time.sleep(2)
                            status_message_placeholder.empty()

                        # call the function to refresh the databases and to update the streamlit hmi reqd
                        logger.info("")
                        logger.info("Call function to clear the caches and update the database derived information")
                        CLEAR_CACHES_AND_CALL_UPDATE_DBASES()

    # ============================================================
    # RENDER THE ID NO PLACEHOLDER
    # ============================================================
    with id_no_placeholder:
        st.text_input(label="next_no_value",
                      key="next_id_no",
                      label_visibility="collapsed",
                      disabled=True)

    # ===========================================================
    # RENDER THE AMOUNT NUMBER PLACEHOLDER
    # ===========================================================
    with amount_number_placeholder:
        st.number_input("Enter amount($): ",
                        min_value=0.00,
                        format="%.02f",
                        step=.01,
                        key="amount_number",
                        label_visibility="collapsed")

    # ===========================================================
    # RENDER THE TODAYS DATE PLACEHOLDER
    # ===========================================================
    with todays_date_placeholder:
        st.text_input(label="todays_date",
                      key="todays_date",
                      label_visibility="collapsed",
                      disabled=True)

    # ============================================================
    # EXPANDER TO GENERATE AND VIEW DATAFRAME SECTION
    # ============================================================
    if st.session_state.amount_number != 0.00:
        with st.expander("Data Summary"):
            logger.info("")
            logger.info("Generate and display the original database dataframe, new record dataframe, and combined "
                        "dataframe.")

            # display the original unposted_ledger dataframe
            st.subheader(f"Original Dataframe of Database: wct_unposted_ledger        Table: unposted_ledger:")
            st.info("Attempt to display the dataframe of database: wct_unposted_ledger  table: unposted_ledger:")
            st.dataframe(st.session_state.df_unposted_ledger, hide_index=True)
            logger.info("Success - Original database dataframe displayed")

            # generate a dataframe based on the users input data
            logger.info("Attempt to generate dataframe containing new record data from user inputs.")
            try:
                df_new_row = pd.DataFrame({
                    "No": [int(st.session_state.next_id_no)],
                    "Project": [selected_project],
                    "Date": [st.session_state.todays_date],
                    "Amount": [str(round(st.session_state.amount_number, 2))],
                    "Supplier": [selected_supplier],
                    "Posted": ["No"],
                    "Photo ID": [st.session_state["storage_id"]],
                    "Type": [selected_type]
                })
                logger.info(f"Success - created new dataframe containing record data from user inputs.")
            except Exception as e:
                logger.info(f"Error - Dataframe creation from user data failed due to error {e}")
                return
            # display the new user input data dataframe
            st.subheader("Unsaved, Modified Dataframe for Database: wct_unposted_ledger     Table: unposted_ledger:")
            st.dataframe(df_new_row, hide_index=True)

            # concatenate the original dataframe and the user data dataframe to create a combined dataframe
            logger.info(f"Attempt to concatenate dataframe by combining original dataframe and new record dataframe.")
            try:
                st.session_state.df_revised = pd.concat([st.session_state.df_unposted_ledger, df_new_row],
                                                        axis=0,
                                                        ignore_index=True)
                logger.info(f"Success - Concatenated dataframe creation was successful.")
            except Exception as e:
                logger.info(f"Error - Concatenated dataframe creation failed due to error {e}")
            st.subheader("Unsaved Modified Dataframe for Database: wct_unposted_ledger Table: unposted_ledger:")
            st.dataframe(st.session_state.df_revised, hide_index=True)

    # =========================================================================
    # EXPANDER CODE SECTION TO ALLOW VIEWING THE ERROR LOG
    # =========================================================================
    with st.expander(" Display the sessions error log information."):
        st.subheader("Session Error Log")
        log_contents = st.session_state.log_stream.getvalue()
        st.code(log_contents if log_contents else "No Error Logs currently exists.", language="log")


##############################################################################
### MAIN CALLING PROGRAM
##############################################################################
if __name__ == "__main__":
    # call functions to read database and generate the streamlit hmi input data
    DATABASE_READ_AND_STREAMLIT_INPUT_GENERATION()
    STREAMLIT_MAIN()
