# Backup Configuration Guide

This guide explains how to set up automated backups for the Birthday Reminder Bot.

## Backup Strategy

The bot uses a tiered backup approach:

1. **Hourly Backups** (retained for 7 days)
   - Created every hour
   - Keeps the last 168 backups (7 days × 24 hours)
   - Fast recovery for recent data loss
   - Location: `backups/hourly/`

2. **Weekly Backups** (retained for 1 year)
   - Created every Monday at 03:00
   - Keeps the last 52 backups (1 year)
   - Weekly snapshots for long-term history
   - Location: `backups/weekly/`

3. **Yearly Backups** (retained permanently)
   - Created on January 1st at 04:00
   - All yearly backups are kept forever
   - Annual archives for permanent record
   - Location: `backups/yearly/`

## Installation on Server

### 1. Copy the backup script to server

```bash
scp backup_manager.py thept@185.221.213.102:/home/thept/bots/HBDReminder/
```

### 2. Make the script executable

```bash
ssh thept@185.221.213.102
chmod +x /home/thept/bots/HBDReminder/backup_manager.py
```

### 3. Set up cron jobs

Edit the crontab:

```bash
crontab -e
```

Add these lines:

```bash
# Hourly backup at the start of each hour (keeps 7 days)
0 * * * * cd /home/thept/bots/HBDReminder && ./venv/bin/python3 backup_manager.py hourly >> /var/log/birthday_bot_backup.log 2>&1

# Weekly backup every Monday at 03:00 (keeps 1 year)
0 3 * * 1 cd /home/thept/bots/HBDReminder && ./venv/bin/python3 backup_manager.py weekly >> /var/log/birthday_bot_backup.log 2>&1

# Yearly backup on January 1st at 04:00 (keeps all)
0 4 1 1 * cd /home/thept/bots/HBDReminder && ./venv/bin/python3 backup_manager.py yearly >> /var/log/birthday_bot_backup.log 2>&1
```

### 4. Verify cron jobs are installed

```bash
crontab -l
```

### 5. Monitor backup logs

```bash
# View last 50 lines
tail -50 /var/log/birthday_bot_backup.log

# Follow logs in real-time
tail -f /var/log/birthday_bot_backup.log
```

## Manual Backup

You can also create backups manually:

```bash
cd /home/thept/bots/HBDReminder
./venv/bin/python3 backup_manager.py hourly
./venv/bin/python3 backup_manager.py weekly
./venv/bin/python3 backup_manager.py yearly
```

## Backup Structure

```
backups/
├── hourly/
│   ├── birthday_bot_hourly_20251204_00.db
│   ├── birthday_bot_hourly_20251204_01.db
│   └── ...
├── weekly/
│   ├── birthday_bot_weekly_2025_week49.db
│   └── ...
└── yearly/
    ├── birthday_bot_yearly_2025.db
    └── ...
```

## Restore from Backup

To restore from a backup:

```bash
# 1. Stop the bot
sudo systemctl stop hbdreminder

# 2. Restore the database
cp /home/thept/bots/HBDReminder/backups/hourly/birthday_bot_hourly_20251204_10.db \
   /home/thept/bots/HBDReminder/birthday_bot.db

# 3. Verify file ownership
sudo chown thept:thept /home/thept/bots/HBDReminder/birthday_bot.db

# 4. Start the bot
sudo systemctl start hbdreminder

# 5. Check status
sudo systemctl status hbdreminder
```

## Disk Space Monitoring

The backup manager logs the size of each backup type:

```bash
# Check current backup sizes
cd /home/thept/bots/HBDReminder
./venv/bin/python3 -c "from backup_manager import BackupManager; m = BackupManager('birthday_bot.db'); sizes = m.get_backup_size(); print('\n'.join(f'{k}: {v/(1024*1024):.2f} MB' for k,v in sizes.items()))"

# Or use du command
du -sh /home/thept/bots/HBDReminder/backups/
du -sh /home/thept/bots/HBDReminder/backups/hourly/
du -sh /home/thept/bots/HBDReminder/backups/weekly/
du -sh /home/thept/bots/HBDReminder/backups/yearly/
```

## Troubleshooting

### Backups not being created

1. Check that cron is running:
```bash
sudo service cron status
```

2. Verify the script has execute permissions:
```bash
ls -la /home/thept/bots/HBDReminder/backup_manager.py
```

3. Check the log file for errors:
```bash
tail -50 /var/log/birthday_bot_backup.log
```

### Database locked error

This usually happens if the bot is writing to the database while backup runs. The script uses `shutil.copy2()` which creates a snapshot without locking.

If issues persist, you can:
1. Stop the bot before backup
2. Create backup
3. Start the bot again

### Running out of disk space

- Check disk usage: `df -h`
- Review backup sizes: `du -sh /home/thept/bots/HBDReminder/backups/`
- Delete old backups manually if needed (oldest hourly backups are auto-deleted)
- Consider moving yearly backups to separate storage

## Best Practices

1. **Monitor logs regularly** - Check `/var/log/birthday_bot_backup.log` weekly
2. **Test restore procedures** - Periodically test that backups can be restored
3. **Keep yearly backups safe** - Consider copying them to another storage
4. **Monitor disk space** - Ensure you have enough space for backups
5. **Rotate logs** - Set up logrotate for `/var/log/birthday_bot_backup.log`

## Logrotate Configuration (Optional)

Create `/etc/logrotate.d/birthday-bot-backup`:

```
/var/log/birthday_bot_backup.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root root
}
```

Then enable it:
```bash
sudo logrotate -f /etc/logrotate.d/birthday-bot-backup
```
