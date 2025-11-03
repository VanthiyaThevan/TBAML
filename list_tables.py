"""
List all SQLite database tables
Shows table names, columns, and row counts
"""

import sqlite3
from app.models.base import get_session_factory
from sqlalchemy import inspect, text


def list_all_tables():
    """List all tables in the SQLite database"""
    
    print("=" * 80)
    print("SQLITE DATABASE TABLES")
    print("=" * 80)
    print()
    
    # Method 1: Direct SQLite query
    conn = sqlite3.connect('tbaml_dev.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f"Total Tables: {len(tables)}\n")
    
    for i, (table_name,) in enumerate(tables, 1):
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print("-" * 80)
        print(f"{i}. Table: {table_name}")
        print(f"   Rows: {row_count}")
        print(f"   Columns: {len(columns)}")
        print()
        print("   Column Details:")
        for col in columns:
            col_id, name, col_type, not_null, default, pk = col
            constraints = []
            if pk:
                constraints.append("PRIMARY KEY")
            if not_null:
                constraints.append("NOT NULL")
            if default:
                constraints.append(f"DEFAULT {default}")
            
            constraint_str = f" [{', '.join(constraints)}]" if constraints else ""
            print(f"     - {name}: {col_type}{constraint_str}")
        print()
    
    conn.close()
    
    # Method 2: Via SQLAlchemy (for reference)
    print("=" * 80)
    print("SQLAlchemy Model Mappings")
    print("=" * 80)
    print()
    
    SessionLocal, engine = get_session_factory()
    inspector = inspect(engine)
    
    sqlalchemy_tables = inspector.get_table_names()
    
    print(f"Tables detected via SQLAlchemy: {len(sqlalchemy_tables)}")
    for table in sqlalchemy_tables:
        print(f"  - {table}")
    print()
    
    # Show which tables correspond to which models
    print("Model to Table Mapping:")
    from app.models.lob import LOBVerification
    
    print(f"  - LOBVerification → {LOBVerification.__tablename__}")
    print()
    
    print("=" * 80)


if __name__ == "__main__":
    list_all_tables()

