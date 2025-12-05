#!/usr/bin/env python3
"""
Backup management script for Birthday Reminder Bot
- Hourly backups (keeps last 168 hours = 7 days)
- Weekly backups (keeps last 52 weeks = 1 year)
- Yearly backups (keeps all)
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BackupManager:
    def __init__(self, db_path: str, backup_base_dir: str = None):
        self.db_path = db_path
        self.backup_base_dir = backup_base_dir or os.path.join(os.path.dirname(db_path), 'backups')
        
        # Create backup directories
        self.hourly_dir = os.path.join(self.backup_base_dir, 'hourly')
        self.weekly_dir = os.path.join(self.backup_base_dir, 'weekly')
        self.yearly_dir = os.path.join(self.backup_base_dir, 'yearly')
        
        for dir_path in [self.hourly_dir, self.weekly_dir, self.yearly_dir]:
            os.makedirs(dir_path, exist_ok=True)
    
    def backup_database(self, backup_type: str = 'hourly') -> bool:
        """
        Create a backup of the database
        
        Args:
            backup_type: 'hourly', 'weekly', or 'yearly'
        
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(self.db_path):
            logger.warning(f"Database not found: {self.db_path}")
            return False
        
        # Determine backup directory and filename
        if backup_type == 'hourly':
            backup_dir = self.hourly_dir
            timestamp_format = '%Y%m%d_%H00'  # Hour precision
        elif backup_type == 'weekly':
            backup_dir = self.weekly_dir
            timestamp_format = '%Y_week%W'  # Week precision
        elif backup_type == 'yearly':
            backup_dir = self.yearly_dir
            timestamp_format = '%Y'  # Year precision
        else:
            logger.error(f"Unknown backup type: {backup_type}")
            return False
        
        try:
            timestamp = datetime.now().strftime(timestamp_format)
            backup_filename = f"birthday_bot_{backup_type}_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Copy database file
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Created {backup_type} backup: {backup_filename}")
            
            # Clean old backups based on type
            self._cleanup_old_backups(backup_dir, backup_type)
            
            return True
        except Exception as e:
            logger.error(f"Error creating {backup_type} backup: {e}")
            return False
    
    def _cleanup_old_backups(self, backup_dir: str, backup_type: str) -> None:
        """Remove old backups based on retention policy"""
        try:
            backups = sorted(os.listdir(backup_dir))
            
            if backup_type == 'hourly':
                # Keep last 168 backups (7 days * 24 hours)
                max_backups = 168
            elif backup_type == 'weekly':
                # Keep last 52 backups (1 year)
                max_backups = 52
            elif backup_type == 'yearly':
                # Keep all yearly backups
                return
            else:
                return
            
            if len(backups) > max_backups:
                to_delete = len(backups) - max_backups
                for backup in backups[:to_delete]:
                    backup_path = os.path.join(backup_dir, backup)
                    os.remove(backup_path)
                    logger.info(f"Deleted old {backup_type} backup: {backup}")
        except Exception as e:
            logger.error(f"Error cleaning old backups: {e}")
    
    def get_backup_size(self) -> dict:
        """Get total size of backups by type"""
        sizes = {'hourly': 0, 'weekly': 0, 'yearly': 0}
        
        for backup_type, backup_dir in [
            ('hourly', self.hourly_dir),
            ('weekly', self.weekly_dir),
            ('yearly', self.yearly_dir)
        ]:
            for filename in os.listdir(backup_dir):
                filepath = os.path.join(backup_dir, filename)
                if os.path.isfile(filepath):
                    sizes[backup_type] += os.path.getsize(filepath)
        
        return sizes


def main():
    """Main function for command-line usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python backup_manager.py <hourly|weekly|yearly>")
        print("Example: python backup_manager.py hourly")
        sys.exit(1)
    
    backup_type = sys.argv[1]
    db_path = os.path.join(os.path.dirname(__file__), 'birthday_bot.db')
    
    manager = BackupManager(db_path)
    success = manager.backup_database(backup_type)
    
    # Print backup sizes
    sizes = manager.get_backup_size()
    print("\nBackup sizes:")
    for btype, size in sizes.items():
        size_mb = size / (1024 * 1024)
        print(f"  {btype}: {size_mb:.2f} MB")
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
