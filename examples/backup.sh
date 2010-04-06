#!/bin/bash
# Use this script as a cron script and run it eg. all 5 minutes:
#*/5 * * * *
DBNAME=ubol3
BACKUPDIR=/media/disk/backup
pg_dump -c  ${DBNAME} | gzip -c > ${BACKUPDIR}/backup_${DBNAME}_$(date "+%Y-%m-%d_%H.%M.%S").sql.gz
