#!/usr/bin/env python3
"""
Restore old data from backup and add is_starred column
"""

import sqlite3
import shutil

def restore_and_migrate():
    old_db = 'trading_plans_backup_20260112_115600.db'
    new_db = 'trading_plans.db'
    
    print("Starting data restoration...")
    
    # Connect to both databases
    old_conn = sqlite3.connect(old_db)
    new_conn = sqlite3.connect(new_db)
    
    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()
    
    try:
        # Get all data from old database
        old_cursor.execute("SELECT * FROM trading_plans")
        rows = old_cursor.fetchall()
        
        # Get column names from old database
        old_cursor.execute("PRAGMA table_info(trading_plans)")
        old_columns = [col[1] for col in old_cursor.fetchall()]
        
        print(f"Found {len(rows)} records to restore")
        
        # Clear new database
        new_cursor.execute("DELETE FROM trading_plans")
        
        # Insert data into new database
        for row in rows:
            # Create a dict from old data
            data = dict(zip(old_columns, row))
            
            # Add is_starred = 0 for old records
            data['is_starred'] = 0
            
            # Insert into new database
            placeholders = ', '.join(['?' for _ in range(len(data))])
            columns = ', '.join(data.keys())
            
            new_cursor.execute(
                f"INSERT INTO trading_plans ({columns}) VALUES ({placeholders})",
                list(data.values())
            )
        
        new_conn.commit()
        print(f"✓ Successfully restored {len(rows)} records!")
        
    except Exception as e:
        print(f"✗ Restoration failed: {e}")
        new_conn.rollback()
    finally:
        old_conn.close()
        new_conn.close()

if __name__ == '__main__':
    restore_and_migrate()
