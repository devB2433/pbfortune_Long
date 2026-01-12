#!/usr/bin/env python3
"""
Add tracking_status column to existing database
Run this script to migrate old database to support the pause tracking feature
"""

import sqlite3
import shutil
from datetime import datetime
import os

def add_tracking_status_column():
    """Add tracking_status column to trading_plans table"""
    
    db_path = 'data/trading_plans.db'
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f'✗ Database not found: {db_path}')
        return False
    
    # Backup database
    backup_dir = 'data/backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_path = f'{backup_dir}/before_tracking_status_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    shutil.copy(db_path, backup_path)
    print(f'✓ Database backed up to: {backup_path}')
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check existing columns
        cursor.execute('PRAGMA table_info(trading_plans)')
        columns = {col[1]: col for col in cursor.fetchall()}
        
        print(f'✓ Current columns: {len(columns)}')
        
        # Add tracking_status column if not exists
        if 'tracking_status' not in columns:
            cursor.execute('''
                ALTER TABLE trading_plans 
                ADD COLUMN tracking_status TEXT DEFAULT 'active'
            ''')
            conn.commit()
            print('✓ Successfully added tracking_status column')
        else:
            print('✓ tracking_status column already exists')
        
        # Verify
        cursor.execute('PRAGMA table_info(trading_plans)')
        all_columns = cursor.fetchall()
        
        print(f'\n✓ Updated columns ({len(all_columns)}):')
        for col in all_columns:
            print(f'  {col[0]+1}. {col[1]:20} {col[2]:10} {"NOT NULL" if col[3] else ""} {("DEFAULT: " + str(col[4])) if col[4] else ""}')
        
        return True
        
    except Exception as e:
        print(f'✗ Error: {e}')
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print('=' * 60)
    print('  Adding tracking_status column to database')
    print('=' * 60)
    print()
    
    success = add_tracking_status_column()
    
    print()
    if success:
        print('✓ Migration completed successfully!')
        print()
        print('Next steps:')
        print('  1. Restart your application: docker-compose restart')
        print('  2. Or redeploy: docker-compose up -d --build')
    else:
        print('✗ Migration failed!')
        print('Please check the error messages above.')
    print()
