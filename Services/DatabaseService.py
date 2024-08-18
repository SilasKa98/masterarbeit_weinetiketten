import mysql.connector
import os
from dotenv import load_dotenv
dotenv_path = '/Masterarbeit_ocr_env/.env'
load_dotenv(dotenv_path=dotenv_path)


class DatabaseService:

    def __init__(self):
        self.mydb = mysql.connector.connect(
            host=os.getenv("HOST"),
            user=os.getenv("USER"),
            password=os.getenv("PASSWORD"),
            database=os.getenv("DATABASE")
        )

    def select_from_table(self, table, selected_cols, condition=None, params=None, join=None, as_dict=False):
        if as_dict:
            connection = self.mydb.cursor(dictionary=True)
        else:
            connection = self.mydb.cursor()

        query = f"SELECT {selected_cols} FROM {table}"

        if join is not None:
            query += f" {join}"

        if condition is not None:
            query += f" WHERE {condition}"

        if params is None:
            connection.execute(query)
        else:
            connection.execute(query, params)

        results = connection.fetchall()
        connection.close()
        return results

    def insert_into_table(self, table, columns, values):
        connection = self.mydb.cursor()
        try:
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(values))})"
            connection.execute(query, tuple(values))
            self.mydb.commit()
            print("Insert successfull.")

        except Exception as e:
            print(f"Error while inserting: {e}")

        finally:
            connection.close()

    def update_table(self, table, columns, values, condition_col, condition_val):
        connection = self.mydb.cursor()
        try:
            set_clause = ', '.join([f"{col} = %s" for col in columns])
            query = f"UPDATE {table} SET {set_clause} WHERE {condition_col} = %s"

            connection.execute(query, values + [condition_val])

            self.mydb.commit()

            print("Update successfull.")

        except Exception as e:
            print(f"Error while updating: {e}")

        finally:
            connection.close()
