# TalkToSQL

TalkToSQL is an CLI tool that lets you query your DB with natural language instead of SQL queries.

## Usage

```sh
$ talktosql learn
Successfully saved the DB Schema Info to /Users/woniesong92/.talktosql_schema_info

$ talktosql ask --q "Find the total sales per author for books published after the year 1800"
SELECT a.name, SUM(b.price * o.quantity) as total_sales
FROM authors a
JOIN books b ON a.id = b.author_id
JOIN orders o ON b.id = o.book_id
WHERE b.publication_date > '1800-12-31'
GROUP BY a.name;
+--------------------+-------------+
|        name        | total_sales |
+--------------------+-------------+
|    J.K. Rowling    |    10.99    |
| George R.R. Martin |    12.99    |
|   J.R.R. Tolkien   |    23.98    |
|  Haruki Murakami   |    14.99    |
|    Jane Austen     |    29.97    |
+--------------------+-------------+
```

![talktosql-demo-gif](https://user-images.githubusercontent.com/2935309/229308121-df48b64a-b54a-425c-a256-f86f33da332e.gif)

## Quickstart

1. Install the package

    ```
    pip install talktosql -U
    ```
2. Set the environment variables

    You can create a `.env` file in your local directory to get kickstarted.

    ```.env
    OPENAI_API_KEY="SOME_API_KEY"
    OPENAI_ORG_ID="SOME_ORG_ID"
    OPENAI_MODEL_NAME="gpt-4"
    TALKTOSQL_DATABASE_URL="mysql://myuser:mypassword@localhost/mydb"
    TALKTOSQL_DATABASE_NAME="mydb"
    ```

    Alternatively, you can run these in your terminal or set these in your terminal config (~/.zshrc)

    ```sh
    export OPENAI_API_KEY="SOME_API_KEY"
    export OPENAI_ORG_ID="SOME_ORG_ID"
    export OPENAI_MODEL_NAME="gpt-4"
    export TALKTOSQL_DATABASE_URL="mysql://myuser:mypassword@localhost/mydb"
    # export TALKTOSQL_DATABASE_URL="postgresql://myuser:mypassword@localhost/mydb"
    export TALKTOSQL_DATABASE_NAME="mydb"
    ```

    - Get the value for `OPENAI_API_KEY` from [OpenAI API Keys](https://platform.openai.com/account/api-keys)
    - Get the value for `OPENAI_ORG_ID` from [OpenAI Org Settings](https://platform.openai.com/account/org-settings)

3. Help TalktoSQL learn your DB Schema. This will save your DB schema info to a file in your home directory (`~/.talktosql_schema_info`)

    ```sh
    talktosql learn
    ```

4. Query your DB in English intead of an SQL query

    ```sh
    talktosql ask --q "how many dogs are there?"
    ```
