#!/usr/bin/env python3
"""
Database migration script to add is_starred column
"""

import sqlite3
import shutil
from datetime import datetime

def migrate_database():
    db_path = 'trading_plans.db'
    backup_path = f'trading_plans_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    # Backup existing database
    try:
        shutil.copy(db_path, backup_path)
        print(f"✓ Backed up database to {backup_path}")
    except FileNotFoundError:
        print("No existing database found, creating new one...")
        return
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if is_starred column exists
        cursor.execute("PRAGMA table_info(trading_plans)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'is_starred' not in columns:
            # Add is_starred column
            cursor.execute("ALTER TABLE trading_plans ADD COLUMN is_starred INTEGER DEFAULT 0")
            print("✓ Added is_starred column")
            
            # Create index
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_starred 
                ON trading_plans(is_starred DESC, created_at DESC)
            ''')
            print("✓ Created star index")
            
            conn.commit()
            print("✓ Migration completed successfully!")
        else:
            print("✓ Database already has is_starred column, no migration needed")
            
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
