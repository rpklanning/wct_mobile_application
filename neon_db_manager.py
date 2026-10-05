import os
import pandas as pd
import psycopg2
from psycopg2 import sql
import logging
import streamlit as st
import uuid
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


# setup error logging capture
logger = logging.getLogger("neon_db_app")

@st.cache_data
def READ_NEON_DB_TABLE_INTO_DATAFRAME(database_to_read, table_to_read):
    """
    Function will read the table of a Neon database and return a pandas dataframe.  Function requires a .env file
    containing the database URL and authorization key.  Databases to be read are limited to wct_data, wct_ledger, and
    wct_unposted_ledger.  Logging of process and errors are captured in an "Error_Log_yyyymmdd_hhmmss.
    :param database_to_read: name of the database to be read from Neon
    :param table_to_read: name of the database table to read from Neon
    :return: df dataframe containing the columns and data records
    """
    logger.info("")
    logger.info("------------------------------------------------------------------------------------")
    logger.info("Module: neon_db_manager.py     Function: READ_NEON_Db_TABLE_INTO_DATAFRAME")
    logger.info(f"ATTEMPTING TO READ FROM NEON DATABASE: {database_to_read} TABLE: {table_to_read}")
    logger.info(f"Assign correct env file KEY based on the database: {database_to_read}.")
    # map to the correct .env file KEY name
    if database_to_read == "wct_unposted_ledger":
        env_key = "NEON_WCT_UNPOSTED_LEDGER_DB_URL"
    elif database_to_read == "wct_ledger":
        env_key = "NEON_WCT_LEDGER_DB_URL"
    elif database_to_read == "wct_data":
        env_key = "NEON_WCT_DATA_DB_URL"
    else:
        logger.error(f"Error - Invalid database name requested: '{database_to_read}'. Not from mapping logic!")
        return None
    logger.info("Success - env_key assigned.")
    logger.info(f"Attempting to read environment variable key '{env_key}' from .env file to get connection string.")
    db_url = os.getenv(env_key)

    # check if the key exists or is completely empty in the .env file
    if not db_url:
        logger.error(f"ERROR: Key '{env_key}' was NOT found or is empty in the .env file.")
        return None

    # extracts the host domain from 'postgresql://user:pass@host/db' while masking the password
    safe_host = db_url.split("@")[-1] if "@" in db_url else "Unknown Host"
    logger.info(f"Success - retrieved connection string from .env. Target host: {safe_host}")

    db_connection = None

    try:
        logger.info("")
        logger.info(f"Attempting to establish network connection to Neon host...")
        db_connection = psycopg2.connect(db_url)
        logger.info("Success - Neon database network connection successfully established.")

        logger.info("")
        logger.info("Attempt to position the cursor and read the database table.")
        with db_connection.cursor() as cursor:
            logger.info(f"Success - Cursor initialized. Executing query on table: '{table_to_read}'")

            query = sql.SQL("SELECT * FROM {};").format(sql.Identifier(table_to_read))
            cursor.execute(query)

            rows = cursor.fetchall()
            # log how many records PostgreSQL returned before building the dataframe
            logger.info(f"Success - Database query executed  and retrieved {len(rows)} raw rows from the database.")

            # get the names of the columns in the database which will be stored in the dataframe
            column_names = [desc[0] for desc in cursor.description]
            # ADDED: Log columns found to help track schema mismatch errors
            logger.debug(f"Table columns discovered: {column_names}")

            # load the data into a Pandas dataframe
            logger.info("")
            logger.info("Attempt to read the database column headers and data into a pandas dataframe")
            df = pd.DataFrame(rows, columns=column_names)
            logger.info(f"Success - completed reading Database: {database_to_read}, Table: {table_to_read} into "
                        f"a dataframe")
            return df

    except Exception as error:
        # FIXED: Added missing 'f' to string, and included the 'error' variable directly in the log
        logger.info("")
        logger.info("Exception routine running")
        logger.error(f"ERROR - CRITICAL failure reading database '{database_to_read}', table '{table_to_read}'. "
                     f"Details: {error}", exc_info=True)
        return df

    finally:
        if db_connection:
            db_connection.close()
            logger.info(f"Database connection to database: {database_to_read} safely closed via finally block.")


def GET_NEON_DATABASE_ENGINE(database_to_write, table_to_write) -> Engine:
    """
    Create a SQLAlchemy engine for Neon/PostgreSQL.

    The connection string can be supplied directly or through
    the NEON_DATABASE_URL environment variable.

    Example:
        postgresql://user:password@ep-example.us-east-2.aws.neon.tech/dbname?sslmode=require
    """
    logger.info("")
    logger.info(f"CREATE DATABASE ENGINE BY ATTEMPTING TO READ FROM DATABASE: {database_to_write} "
                f"TABLE: {table_to_write}")
    logger.info(f"Assign correct env file KEY based on the database: {database_to_write}.")
    # map to the correct .env file KEY name
    if database_to_write == "wct_unposted_ledger":
        env_key = "NEON_WCT_UNPOSTED_LEDGER_DB_URL"
    elif database_to_write == "wct_ledger":
        env_key = "NEON_WCT_LEDGER_DB_URL"
    elif database_to_write == "wct_data":
        env_key = "NEON_WCT_DATA_DB_URL"
    else:
        raise ValueError(f"Invalid database name requested: '{database_to_write}'. "
        f"Not found in database mapping."
        )
        # TODO remove
        #logger.error(f"Invalid database name requested: '{database_to_write}'. Not from mapping logic!")
        #return False

    logger.info(f"Attempting to read environment variable key '{env_key}' from .env file.")
    db_url = os.getenv(env_key)

    # check if the key exists or is completely empty in the .env file
    if not db_url:
        raise ValueError(
            f"CRITICAL: Environment variable '{env_key}' "
            f"was not found or is empty."
        )

    # extracts the host domain from 'postgresql://user:pass@host/db' while masking the password
    safe_host = db_url.split("@")[-1] if "@" in db_url else "Unknown Host"
    logger.info(f"Successfully retrieved connection string from .env. Target host: {safe_host}")
    logger.info("Database engine successfully created!")
    logger.info("")

    return create_engine(db_url, pool_pre_ping=True)


def UPLOAD_DATAFRAME_TO_NEON_DATABASE(
        df: pd.DataFrame,
        database_name: str,
        table_name: str,
        database_url: Optional[str] = None):
    """
    Replace a PostgreSQL/Neon table with the contents of a dataFrame.

    Process:
        1. Create a staging table using the target table's structure.
        2. Copy the dataframe into the staging table.
        3. Verify all dataframe rows were copied.
        4. Replace the target table contents from staging.
        5. Verify the final row count.
        6. Commit the transaction.

    Parameters
    ----------
    df:
        DataFrame containing the replacement data.

    database_name:
        Database name, e.g. "wct_unposted_ledger".
        This is checked against the connected database.

    table_name:
        Target table, e.g. "unposted_ledger".

    database_url:
        Optional Neon/PostgreSQL connection string.
        If omitted, NEON_DATABASE_URL is used.

    Returns
    -------
    bool
        Upload status is completed (True) or not completed (False).

    Raises
    ------
    ValueError
        If parameters are invalid or the row count verification fails.

    Exception
        Any database exception causes the transaction to roll back.
    """
    logger.info("")
    logger.info("------------------------------------------------------------------------------------")
    logger.info("Module: neon_db_manager.py     Function: UPLOAD_DATAFRAME_TO_NEON_DATABASE")
    logger.info(f"ATTEMPT TO UPDATE DATABASE: {database_name} TABLE: {table_name}")

    # Validate function input information.
    try:
        logger.info("Validate the dataframe none, type, and size information.")
        if df is None:
            raise ValueError("DataFrame being passed cannot be None.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame.")

        if df.empty:
            raise ValueError("DataFrame being passed cannot be empty.")
        logger.info("Dataframe none, type, and size are valid.")

        logger.info("")
        logger.info("Validate the database name and table name.")
        if not database_name:
            raise ValueError(
                "The name of the Neon database 'database_name' is required.")

        if not table_name:
            raise ValueError(
                "The name of the Neon database table 'table_name' is required.")
        logger.info("Validated - Database name and table name.")

        # Database and table names are SQL identifiers rather than SQL values.
        # They cannot be safely passed as SQL parameters, so validate them before
        # using them in SQL statements. _validate_identifier() should enforce the
        # application's allowed characters, length, and PostgreSQL identifier rules.
        logger.info("")
        msg = "Validate that database name and table name can be safety passed to SQL-characters, length, identifier."
        logger.info(msg)
        _validate_identifier(database_name)
        _validate_identifier(table_name)
        logger.info("Validated - Database name and table name are acceptable to SQL!")

    except (ValueError, TypeError) as e:
        logger.error(
            "Dataframe and database validation failed. "
            "database_name=%s, table_name=%s, error=%s",
            database_name,
            table_name,
            e,
        )
        return False

    logger.info(
        "Function data input validation has passed. "
        "database_name=%s, table_name=%s",
        database_name,
        table_name,
    )

    # call the function to get the database connection engine
    neon_engine = GET_NEON_DATABASE_ENGINE(database_name, table_name)

    # create the staging table name
    logger.info(f"Attempt to generate a staging table name in the database: {table_name}")
    staging_table = f"_{table_name}_staging_{uuid.uuid4().hex[:12]}"
    logger.info(f"Success - created a staging table name: {staging_table}.  No data has been written.")

    # get the number of rows of the dataframe to be loaded into the staging table
    logger.info("Get the no of records in the dataframe to be loaded into the database:")
    df_expected_rows = len(df)
    logger.info(f"Dataframe length = {df_expected_rows}")


    logger.info("")
    logger.info("Attempting to connect to Neon database...")
    try:
        with neon_engine.connect() as connection:
            logger.info("Success - connected to Neon database.")

            # ------------------------------------------------------------------------------------------------------
            # Verify that program is connected to the requested database:database_name and raise error in incorrect
            # ------------------------------------------------------------------------------------------------------
            logger.info("")
            logger.info(f"Check that the program is connected to database: {database_name}.")
            connected_database = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

            if connected_database != database_name:
                raise ValueError(f"Error - Connected to database: '{connected_database} but expected '{database_name}'.")
            else:
                logger.info(f"Validated - program is connected to to correct database: '{connected_database}'.")

            # --------------------------------------------------------------------------------------------------------------
            # Verify target table: table_name (to be modified) exists in the database and raise error if it does not exists.
            # --------------------------------------------------------------------------------------------------------------
            logger.info("")
            logger.info(f"Check if the table: {table_name} to be modified exists in database: {database_name}.")

            target_exists = connection.execute(
                text("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_name = :table_name
                    )
                """),
                {"table_name": table_name},
            ).scalar_one()

            if not target_exists:
                raise ValueError(
                    f"Error - Public table: {table_name} to be modified does not exist in database: {database_name}."
                )
            else:
                logger.info(f"Validated - Public table: {table_name} to be modified exists in database: "
                            f"{database_name}.")

            # -----------------------------------------------------
            # Create staging table with the same columns/types as
            # the target table, but without copying the data.
            #
            # LIKE copies the table structure, including:
            #   - column definitions
            #   - defaults
            #   - identity definitions
            #   - indexes when INCLUDING INDEXES is used
            # -----------------------------------------------------
            logger.info("")
            msg = f"Attempt to create staging table: {staging_table} with structure from existing table: {table_name}."
            logger.info(msg)

            connection.execute(
                text(
                    f"""
                    CREATE TABLE public."{staging_table}"
                    (
                        LIKE public."{table_name}"
                        INCLUDING DEFAULTS
                        INCLUDING IDENTITY
                        INCLUDING GENERATED
                        INCLUDING CONSTRAINTS
                    )
                    """
                )
            )

            # Commit staging-table creation so pandas can see it
            # through its own SQLAlchemy connection.
            connection.commit()

            logger.info(f"Success - Staging table: {staging_table} created in database: {database_name}.")

            # -----------------------------------------------------
            # Load DataFrame into staging table.
            #
            # pandas.to_sql uses SQLAlchemy and performs the insert
            # through the same Neon database.
            # -----------------------------------------------------
            logger.info("")
            logger.info(f"Attempt to load dataframe into staging table: {staging_table}.")
            df.to_sql(
                staging_table,
                con=neon_engine,
                schema="public",
                if_exists="append",
                index=False,
                method="multi",
                chunksize=500,
            )
            logger.info(f"Success - Dataframe loaded into staging table: {staging_table}.")

            # ---------------------------------------------------------------------------------------------------
            # Verify every DataFrame row made it into staging and that the staging db is 1 more than the orig db.
            # ---------------------------------------------------------------------------------------------------
            logger.info("")
            msg = ("Check that the number of rows in dataframe is equal the number of rows in staging table: "
                        "{staging_table}.")
            logger.info(msg)

            with neon_engine.begin() as verify_connection:
                staging_db_row_count = verify_connection.execute(
                    text(
                        f'''
                        SELECT COUNT(*)
                        FROM public."{staging_table}"
                        '''
                    )
                ).scalar_one()
            logger.info(f"Number of rows in dataframe to be replace in database table = {df_expected_rows}")
            logger.info(f"Number of rows in staging table {staging_table} =  {staging_db_row_count}")

            if staging_db_row_count != df_expected_rows:
                raise RuntimeError(
                    f"Error - Staging table to dataframe row count mismatch.  Reqd: Staging = dataframe."
                    f"Dataframe {df } row count: {df_expected_rows}, "
                    f"but Staging table {staging_table} contains: {staging_db_row_count} rows."
                )
            else:
                logger.info(f"Validated - that the number of rows in staging table {staging_table} match the number of"
                            f" rows in the dataframe.")

            # confirm the number of rows in the staging table is 1 more than the number of rows in the database table
            with neon_engine.begin() as verify_connection:
                db_table_row_count = verify_connection.execute(
                    text(
                        f'''
                        SELECT COUNT(*)
                        FROM public."{table_name}"
                        '''
                    )
                ).scalar_one()

            logger.info(f"Number of rows in Database: {database_name} Table: {table_name}: {db_table_row_count}")

            # check that the row count of the staging db - original db table is 1
            if (staging_db_row_count - db_table_row_count) != 1:
                raise RuntimeError(
                    f"Error - Staging table to original table row count mismatch.  Reqd: Staging = 1 + original."
                    f"Original table: {table_name} row count: {db_table_row_count}, "
                    f"but Staging table: {staging_table} contains: {staging_db_row_count} rows."
                )
            else:
                logger.info(f"Validated - Staging table {staging_table} row count is 1 more than the number of rows "
                            f"in the original table: {table_name}.")

            # -----------------------------------------------------
            # Begin the replacement transaction.
            #
            # DELETE + INSERT keeps the existing table itself
            # intact, including permissions and dependencies.
            # -----------------------------------------------------
            logger.info("")
            logger.info(f"Attempting to delete database: {database_name} table: {table_name}.")
            with neon_engine.begin() as replace_connection:
                replace_connection.execute(
                    text(
                        f'''
                        DELETE FROM public."{table_name}"
                        '''
                    )
                )
                logger.info("Success - Deleted database: {database_name} table: {table_name}.")

                logger.info("")

                msg = (f"Attempt to replace database: {database_name} table: {table_name} data with staging "
                       f" table: {staging_table}.")
                logger.info(msg)
                if df_expected_rows > 0:
                    replace_connection.execute(
                        text(
                            f'''
                            INSERT INTO public."{table_name}"
                            SELECT *
                            FROM public."{staging_table}"
                            '''
                        )
                    )
                msg = (f"Success - replaced database: {database_name} table: {table_name} with data from staging"
                       f" table: {staging_table}.")
                logger.info(msg)

                # Verify the modified table row count while still inside the transaction. If this fails, the transaction
                # rolls back automatically.
                logger.info("")
                logger.info("Check the mod database: {database_name} table: {table_name} row count vs the df size}")
                msg = (f" Read modified database: {database_name} table: {table_name} data to get the row count.")
                logger.info(msg)
                mod_table_final_count = replace_connection.execute(
                    text(
                        f'''
                        SELECT COUNT(*)
                        FROM public."{table_name}"
                        '''
                    )
                ).scalar_one()
                logger.info(f"Modified database: {database_name} table: {table_name} row count: {mod_table_final_count}")
                logger.info(f"Dataframe row count: {df_expected_rows}")

                if mod_table_final_count != df_expected_rows:
                    raise RuntimeError(
                        f"Error - Modified table: {table_name} from staging table: {staging_table } row count mismatch."
                        f" Expected {df_expected_rows}, "
                        f"but found {mod_table_final_count}."
                    )
                else:
                    logger.info(f"Validated - database: {database_name} mod table: {table_name} row count matches the "
                                f"original dataframe row count.")

            # -----------------------------------------------------
            # Drop staging table after successful replacement.
            # -----------------------------------------------------
            logger.info("")
            logger.info("Attempt to delete staging table: {staging_table}.")
            with neon_engine.begin() as cleanup_connection:
                cleanup_connection.execute(
                    text(
                        f'''
                        DROP TABLE IF EXISTS public."{staging_table}"
                        '''
                    )
                )
            logger.info("Success - deleted staging table: {staging_table}.")
            return True

    except Exception as e:
        logger.info("")
        logger.info(f"Error Recovery Routine Initiated due to error {e}")
        # Best effort cleanup. The original table remains
        # untouched if the replacement transaction failed.
        try:
            connection.rollback()
            connection.execute(
                text(
                    f'''
                    DROP TABLE IF EXISTS public."{staging_table}"
                    '''
                )
            )
            connection.commit()
            logger.info("Success - Completed rollback of transaction")

        except Exception as e:
            logger.info(f"Error - Unable to replace table: {table_name} with staging table: {staging_table} and delete "
                        f"the staging table due to error: {e}")

        raise

    finally:
        logger.info("Attempt to dispose of the database engine.")
        neon_engine.dispose()
        logger.info("Success - disposed of database engine.")



# TODO make uppercase
def _validate_identifier(identifier: str) -> None:
    """
    Validate a PostgreSQL identifier.

    This intentionally permits only letters, numbers and underscores.
    """
    if not identifier:
        raise ValueError("Identifier cannot be empty.")

    if not identifier.replace("_", "").isalnum():
        raise ValueError(
            f"Invalid PostgreSQL identifier: {identifier!r}"
        )

    if identifier[0].isdigit():
        raise ValueError(
            f"PostgreSQL identifier cannot start with a digit: {identifier!r}"
        )