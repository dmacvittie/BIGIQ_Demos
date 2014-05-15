#!/bin/bash

echo
echo
echo F5 BIG-IQ Backup and pruning installer
echo This system is designed to show how APIs work with BIG-IQ
echo and conveniently also implements regular backups and pruning

FREQUENCY="daily weekly monthly"
DOW="Monday Tuesday Wednesday Thursday Friday Saturday Sunday"
PYTHON=$(which python)
USER=$(whoami)

echo 
echo How often should we perform backups of your BIG-IPs?
select opt in $FREQUENCY; do
    if [ "$opt" = "daily" ]; then
        echo Daily backups
        break;
    elif [ "$opt" = "weekly" ]; then
        echo Weekly backups
        echo What day of week should we back up?
        select dow in $DOW; do
	    if [ "$dow" = "Monday" ]; then
		ndow=1
		break;
            elif [ "$dow" = "Tuesday" ]; then
		ndow=2
		break;
            elif [ "$dow" = "Wednesday" ]; then
		ndow=3
		break;
            elif [ "$dow" = "Thursday" ]; then
		ndow=4
		break;
            elif [ "$dow" = "Friday" ]; then
		ndow=5
		break;
            elif [ "$dow" = "Saturday" ]; then
		ndow=6
		break;
            elif [ "$dow" = "Sunday" ]; then
                ndow=0
		break;
            else
                echo "Invalid option, please retry.";
            fi
        done
        echo Backups will be performed on "$dow"s. "$ndow"
        break;
    elif [ "$opt" = "monthly" ]; then
        echo Monthly backups
        echo What day of the month should we perform backups?
        
        while [[ (! $dom =~ ^[0-9]+$)  && ($dom -le "0") || ($dom -ge "29") ]] ; do
            echo Please enter day of month \(1 to 28\) to perform backup. 
            read dom
        done

        break;
    else
	echo Not a valid frequency please choose the correct number.
    fi
done

echo What hour \(24 hour clock\) would you like to perform backups? 

hour="-1"
while [[ (! $hour =~ ^[0-9]+$)  ||  ($hour -lt "0") ||  ($hour -gt "23") ]] ; do
    echo Please enter hour from 0 to 23.
    read hour
done


echo Backups will be performed at "$hour"\:00

echo How many days \(1 to 365\) should we retain each backup?

age="-1"
while [[ (! $age =~ ^[0-9]+$)  ||  ($age -le "0") ||  ($age -gt "365") ]] ; do
    echo Please enter days to keep backups from 1 to 365.
    read age
done

echo Keeping backups "$age" days before deleting.

echo BIG-IQ APIs require use of username and password. This is a sample, so we store them in the cron file. For production use, another option should be considered.
echo No validation is performed on these entries. If there is a problem, please check /etc/cron.d/biqbackup.cron to edit them.


echo Enter BIQ Username \(admin\)\:
read username
if [ "$username" = "" ]; then
    username="admin"
fi

echo Enter BIQ Password \(admin\)\:
read password
if [ "$password" = "" ]; then
    password="admin"
fi

echo Enter IPv4 Address of BIG-IQ:
read address

cronPruneCmd="$PYTHON $PWD/PruneBackupList.py --user $username --password $password --address $address --age $age"
cronBackupCmd="$PYTHON $PWD/BackupSystems.py --user $username --password $password --address $address"


if [ "$opt" = "daily" ]; then
    cronprune="00 $hour * * * $cronPruneCmd"
    cronbackup="30 $hour * * * $cronBackupCmd"


elif [ "$opt" = "weekly" ]; then

    cronprune="00 $hour * * $ndow $cronPruneCmd"
    cronbackup="30 $hour * * $ndow $cronBackupCmd"
 

elif [ "$opt" = "monthly" ]; then

    cronprune="00 $hour $dom * * $cronPruneCmd"
    cronbackup="30 $hour $dom * * $cronBackupCmd"

fi


# Now install the command into cron. 
( crontab -l | grep -v "$cronPruneCmd" ; echo "$cronprune" ) | crontab -
( crontab -l | grep -v "$cronBackupCmd" ; echo "$cronbackup" ) | crontab -

echo The schedule has been installed in the current users cron. If you move the python scripts, please re-run this installer from the new directory.
