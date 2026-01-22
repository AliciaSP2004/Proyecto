#!/bin/bash
if systemctl is-active --quiet apache2; then
    echo "$(date): Apache OK" >> /var/log/apache_monitor.log
else
    echo "$(date): Apache CAÍDO" >> /var/log/apache_monitor.log
    sudo systemctl restart apache2
fi
