"""Text-to-SQL conversion module for natural language to SQL queries.

This module provides:
- DatabaseSchema: Schema definition for database tables
- SQLQuery: Data class for SQL query results
- TextToSQLConverter: Converts natural language queries to SQL

Security features:
- Whitelist validation for tables and columns
- Rejection of dangerous SQL operations (DROP, DELETE, etc.)
- SQL syntax validation using SQLGlot
"""

from dataclasses import dataclass
from typing import Optional
import sqlglot
from sqlglot import parse, exp


# Custom exceptions
class ValidationError(Exception):
    """Raised when SQL validation fails."""

    pass


class SQLGenerationError(Exception):
    """Raised when SQL generation fails."""

    pass


@dataclass
class ColumnInfo:
    """Information about a database column.

    Attributes:
        name: Column name
        type: Column data type (e.g., TEXT, INTEGER, REAL)
        description: Human-readable description of the column
    """

    name: str
    type: str
    description: str = ""


@dataclass
class TableInfo:
    """Information about a database table.

    Attributes:
        name: Table name
        columns: List of columns in the table
    """

    name: str
    columns: list[ColumnInfo]


class DatabaseSchema:
    """Schema definition for a database.

    Provides table lookup and validation capabilities.

    Attributes:
        tables: List of TableInfo objects defining the schema
    """

    def __init__(self, tables: list[TableInfo]):
        """Initialize database schema.

        Args:
            tables: List of TableInfo objects
        """
        self.tables = tables
        self._table_map = {table.name: table for table in tables}

    def get_table(self, name: str) -> Optional[TableInfo]:
        """Retrieve a table by name.

        Args:
            name: Table name to look up

        Returns:
            TableInfo if found, None otherwise
        """
        return self._table_map.get(name)

    def get_all_table_names(self) -> set[str]:
        """Get all table names in the schema.

        Returns:
            Set of table names
        """
        return set(self._table_map.keys())

    def get_column_names(self, table_name: str) -> set[str]:
        """Get all column names for a table.

        Args:
            table_name: Name of the table

        Returns:
            Set of column names, empty set if table not found
        """
        table = self.get_table(table_name)
        if table is None:
            return set()
        return {col.name for col in table.columns}

    def get_all_columns(self) -> dict[str, set[str]]:
        """Get all columns for all tables.

        Returns:
            Dictionary mapping table names to column name sets
        """
        result = {}
        for table in self.tables:
            result[table.name] = self.get_column_names(table.name)
        return result


@dataclass
class SQLQuery:
    """Result of a text-to-SQL conversion.

    Attributes:
        sql: The generated SQL string
        explanation: Natural language explanation of the query logic
        confidence: Confidence score (0-1) for the generated SQL
    """

    sql: str
    explanation: str
    confidence: float = 0.5


class TextToSQLConverter:
    """Converts natural language queries to SQL.

    Uses an LLM client for generation and SQLGlot for validation.

    Attributes:
        schema: DatabaseSchema defining available tables and columns
        llm_client: LLM client for generating SQL from natural language
        max_retries: Maximum number of retries for SQL generation
    """

    # Forbidden SQL operations that could damage data
    FORBIDDEN_OPERATIONS = {
        "DROP",
        "DELETE",
        "TRUNCATE",
        "ALTER",
        "INSERT",
        "UPDATE",
        "REPLACE",
        "CREATE",
        "GRANT",
        "REVOKE",
    }

    def __init__(self, schema: DatabaseSchema, llm_client, max_retries: int = 2):
        """Initialize TextToSQLConverter.

        Args:
            schema: DatabaseSchema with table definitions
            llm_client: LLM client with generate(prompt) -> str method
            max_retries: Maximum retry attempts for SQL generation
        """
        self.schema = schema
        self.llm_client = llm_client
        self.max_retries = max_retries

    def convert(self, natural_query: str) -> SQLQuery:
        """Convert natural language query to SQL.

        Args:
            natural_query: Natural language query string

        Returns:
            SQLQuery containing the generated SQL, explanation, and confidence

        Raises:
            SQLGenerationError: If conversion fails after retries
            ValidationError: If generated SQL fails validation
        """
        if not natural_query or not natural_query.strip():
            raise SQLGenerationError("Empty query provided")

        # Generate SQL with retries
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                sql, explanation = self._generate_sql(natural_query, attempt)
                # Validate the generated SQL
                self._validate_sql(sql)
                # Return with confidence based on attempt
                confidence = 0.95 if attempt == 0 else 0.85 - (attempt * 0.1)
                return SQLQuery(sql=sql, explanation=explanation, confidence=max(0.5, confidence))
            except ValidationError as e:
                last_error = e
                if attempt < self.max_retries:
                    continue
                raise SQLGenerationError(f"SQL validation failed after {self.max_retries + 1} attempts: {e}")
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    continue
                raise SQLGenerationError(f"SQL generation failed after {self.max_retries + 1} attempts: {e}")

        raise SQLGenerationError(f"SQL generation failed: {last_error}")

    def _generate_sql(self, query: str, attempt: int) -> tuple[str, str]:
        """Generate SQL from natural language query using LLM.

        Args:
            query: Natural language query
            attempt: Current attempt number (0-based)

        Returns:
            Tuple of (sql_string, explanation)
        """
        prompt = self._build_prompt(query, attempt)
        response = self.llm_client.generate(prompt)

        # Parse the LLM response to extract SQL and explanation
        return self._parse_llm_response(response)

    def _build_prompt(self, query: str, attempt: int) -> str:
        """Build the prompt for the LLM.

        Args:
            query: Natural language query
            attempt: Current attempt number

        Returns:
            Formatted prompt string
        """
        schema_description = self._format_schema()

        prompt = f"""You are a Text-to-SQL converter for a manufacturing database.
Convert the following natural language query to SQL.

Available Schema:
{schema_description}

Rules:
- Only use tables and columns from the schema above
- Use SQLite-compatible SQL syntax
- For date operations, use date() and datetime() functions as needed
- Always use proper JOIN syntax with ON clauses
- Return only SELECT queries (no INSERT, UPDATE, DELETE, DROP, etc.)

Natural Language Query: {query}

Respond in the following format:
SQL: <your SQL query here>
EXPLANATION: <brief explanation of what the query does>

Example:
Query: "Show OEE for each line yesterday"
SQL: SELECT line, oee FROM production_daily WHERE date = date('now', '-1 day')
EXPLANATION: This query retrieves the OEE values for each production line from yesterday.
"""
        return prompt

    def _format_schema(self) -> str:
        """Format the database schema for the prompt.

        Returns:
            Formatted schema string
        """
        lines = []
        for table in self.schema.tables:
            lines.append(f"\nTable: {table.name}")
            for col in table.columns:
                desc = f" - {col.description}" if col.description else ""
                lines.append(f"  - {col.name} ({col.type}){desc}")
        return "\n".join(lines)

    def _parse_llm_response(self, response: str) -> tuple[str, str]:
        """Parse LLM response to extract SQL and explanation.

        Args:
            response: Raw LLM response string

        Returns:
            Tuple of (sql_string, explanation)

        Raises:
            SQLGenerationError: If response format is invalid
        """
        lines = response.strip().split("\n")

        sql = None
        explanation = None

        for line in lines:
            line = line.strip()
            if line.startswith("SQL:"):
                sql = line[4:].strip()
            elif line.startswith("EXPLANATION:"):
                explanation = line[12:].strip()

        # If SQL not found with prefix, check if response is a standalone SQL statement
        if sql is None:
            # Check if the response looks like a SQL statement (starts with SELECT, WITH, etc.)
            response_upper = response.strip().upper()
            if response_upper.startswith("SELECT") or response_upper.startswith("WITH"):
                sql = response.strip()
                explanation = "Generated SQL query"
            else:
                raise SQLGenerationError(f"Invalid LLM response format: missing SQL. Response: {response}")

        if explanation is None:
            explanation = "Generated SQL query"

        return sql, explanation

    def _validate_sql(self, sql: str) -> None:
        """Validate SQL for syntax correctness and security.

        Args:
            sql: SQL string to validate

        Raises:
            ValidationError: If SQL is invalid or insecure
        """
        # Check for forbidden operations
        sql_upper = sql.upper()
        for forbidden in self.FORBIDDEN_OPERATIONS:
            if f" {forbidden} " in sql_upper or sql_upper.startswith(forbidden):
                raise ValidationError(f"Forbidden SQL operation: {forbidden}")

        # Parse and validate SQL syntax using SQLGlot
        try:
            parsed = parse(sql, dialect="sqlite")
            if not parsed:
                raise ValidationError("Failed to parse SQL - empty result")
        except Exception as e:
            raise ValidationError(f"Invalid SQL syntax: {e}")

        # Validate table and column references against schema
        self._validate_table_references(sql)

    def _validate_table_references(self, sql: str) -> None:
        """Validate that SQL only references known tables and columns.

        Args:
            sql: SQL string to validate

        Raises:
            ValidationError: If unknown tables or columns are referenced
        """
        # Extract table references from the SQL
        try:
            parsed = parse(sql, dialect="sqlite")[0]

            # Get all table references
            tables_in_schema = self.schema.get_all_table_names()
            columns_in_schema = self.schema.get_all_columns()

            # Walk the parsed AST to find table and column references
            for node in parsed.walk():
                if isinstance(node, exp.Table):
                    table_name = node.name
                    if table_name not in tables_in_schema:
                        raise ValidationError(f"Unknown table: {table_name}")

                if isinstance(node, exp.Column):
                    table = node.table
                    column_name = node.name

                    # If table is specified, validate column against that table
                    if table:
                        if table in columns_in_schema:
                            if column_name not in columns_in_schema[table]:
                                raise ValidationError(f"Unknown column: {column_name} in table {table}")
                    else:
                        # Column without table qualifier - check if exists in any table
                        # But allow unqualified columns in ORDER BY as they may be aliases
                        parent = node.parent
                        # exp.Ordered is used for individual columns in ORDER BY
                        if not isinstance(parent, exp.Ordered):
                            # Not in ORDER BY context - check if column exists in any table
                            found_in_any_table = False
                            for table_name, col_names in columns_in_schema.items():
                                if column_name in col_names:
                                    found_in_any_table = True
                                    break
                            if not found_in_any_table:
                                raise ValidationError(f"Unknown column: {column_name}")

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to validate SQL: {e}")