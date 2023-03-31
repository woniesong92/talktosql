import argparse
import os
import openai
from pathlib import Path
from dotenv import load_dotenv
from termcolor import colored
from prettytable import PrettyTable
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError


DEFAULT_DB_SCHEMA_INFO_FILE_NAME = ".talktosql_schema_info"
SQL_QUERY_COLOR = "blue"
SQL_RESULT_HEADER_COLOR = "cyan"
FILE_PATH_COLOR = "red"
COMMAND_COLOR = "yellow"
COMMAND_LEARN = "learn"
COMMAND_ASK = "ask"


class TalkToSql:
    def __init__(self):
        load_dotenv()
        openai.organization = os.environ["OPENAI_ORG_ID"]
        openai.api_key = os.environ["OPENAI_API_KEY"]
        self.openai_model_name = os.environ["OPENAI_MODEL_NAME"]
        self.db_name = os.environ["TALKTOSQL_DATABASE_NAME"]
        self.db_engine = create_engine(os.environ["TALKTOSQL_DATABASE_URL"])
        self.openai_client = openai
        self.db_schema_info = ""

    def get_sql_query(self, q):
        """
        Given a query in natural language, return a valid SQL query.

        :param q: query in natural language (e.g. "how many dogs are there?").
        :return: valid SQL query (e.g. "SELECT COUNT(*) FROM dogs;").
        """

        system_prompt = """
            You are the world's best SQL expert. Help me convert natural language to valid SQL queries. Only respond with valid SQL queries, nothing else.
            You must learn the column names based on the information the user gives you and build valid SQL queries. Never guess the column names.
            These are the examples:

            query: get all people names
            answer: SELECT name from people;

            query: get all cars whose owner name is aaron
            answer: SELECT c.* FROM people p JOIN cars c ON p.id = c.owner_id WHERE p.name = 'aaron';
        """

        user_prompt = f"""
            This is my database information:
            {self.db_schema_info}

            query: {q}
            answer:
        """

        completion = self.openai_client.ChatCompletion.create(
            model=self.openai_model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        return completion.choices[0].message.content

    def execute(self, sql_query):
        """
        Execute the given SQL Query after connecting to the specified DB URL.

        :param sql_query: valid SQL query
        :return: result of the execution
        """

        with self.db_engine.connect() as connection:
            return connection.execute(text(sql_query))

    def set_db_schema_info(self):
        """
        Store the DB schema info from the file created from the "learn" command

        :param db_schema_info_file_path: file path of the DB schema info
        :return: void
        """

        with open(self.get_schema_info_file_path(), "r") as f:
            self.db_schema_info = f.read()

    def learn(self):
        """
        Learn the schema of the DB specified with the DB URL and store it into a file.
        This file will later be used to provide context to the LLM to get valid SQL queries.

        :param db_schema_info_file_path: file path of the DB schema info
        :return: void
        """
        sql_query = self._get_learn_sql_query()
        result = self.execute(sql_query)
        schema_info_file_path = self.get_schema_info_file_path()
        self._write_learn_result_to_file(result, schema_info_file_path)

    def print_result(self, result):
        """
        Print the result of a SQL execution in a table format.

        :param result: SQL execution result
        :return: void
        """

        print(self._get_table_from_result(result, is_colored=True))

    def _write_learn_result_to_file(self, result, path):
        with open(path, "w") as f:
            table = self._get_table_from_result(result)
            f.write(table.get_string())
            print(
                f"Successfully saved the DB Schema Info to {colored(path, FILE_PATH_COLOR)}"
            )

    def get_schema_info_file_path(self):
        return Path.home() / DEFAULT_DB_SCHEMA_INFO_FILE_NAME

    def _get_table_from_result(self, result, is_colored=False):
        column_names = result.keys()

        table = PrettyTable(field_names=column_names)
        if is_colored:
            table.field_names = [
                colored(column_name, SQL_RESULT_HEADER_COLOR)
                for column_name in column_names
            ]

        for row in result:
            table.add_row(row)
        return table

    def _get_env_var(self, var_name):
        value = os.environ.get(var_name)
        if value is None:
            raise ValueError(f"Environment variable '{var_name}' does not exist. Did you forget to set the environment variable?")
        return value

    def _get_learn_sql_query(self):
        db_url = os.environ["TALKTOSQL_DATABASE_URL"]
        if "mysql://" in db_url:
            return f"""
                SELECT table_name, column_name, data_type, is_nullable, column_key, column_default, extra
                FROM information_schema.columns
                WHERE table_schema = '{self.db_name}'
            """
        elif "postgresql://" in db_url:
            return f"""
                SELECT table_name, column_name, data_type, is_nullable, character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_catalog = '{self.db_name}';
            """
        else:
            print(f"The database specified in the URL {colored(db_url, FILE_PATH_COLOR)} is not supported")
            return ""


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--silent",
        action="store_true",
        required=False,
        help="If present, SQL queries are not printed.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True, metavar="command")

    subparsers.add_parser(COMMAND_LEARN)

    ask_parser = subparsers.add_parser(COMMAND_ASK)
    ask_parser.add_argument(
        "--q", type=str, required=True, help="Your query in natural language"
    )

    return parser.parse_args()


def handle_ask_command(args, talk_to_sql):
    try:
        talk_to_sql.set_db_schema_info()
    except FileNotFoundError:
        print(
            f"File not found: {colored(talk_to_sql.get_schema_info_file_path(), FILE_PATH_COLOR)}\nDid you forget to run the command {colored('talktosql learn', COMMAND_COLOR)}?"
        )
        return

    sql_query = ""
    try:
        sql_query = talk_to_sql.get_sql_query(args.q)
        if not args.silent:
            print(colored(sql_query, SQL_QUERY_COLOR))
    except Exception as e:
        print(
            f"An error occured while converting the query into a SQL Query. Error details:", e
        )

    try:
        result = talk_to_sql.execute(sql_query)
    except ProgrammingError:
        print(
            f"An error occurred while executing the SQL query. Try using a different query or a better model (e.g. GPT-4 instead of GPT-3.5-turbo)"
        )
        return

    talk_to_sql.print_result(result)


def main():
    args = parse_arguments()
    command = args.command
    try:
        talk_to_sql = TalkToSql()
    except KeyError as e:
        missing_env_var = e.args[0]
        print(f"Did you forget to set the environment variable {colored(missing_env_var, FILE_PATH_COLOR)}?")
        return

    if command == COMMAND_LEARN:
        talk_to_sql.learn()
    elif command == COMMAND_ASK:
        handle_ask_command(args, talk_to_sql)


if __name__ == "__main__":
    main()
