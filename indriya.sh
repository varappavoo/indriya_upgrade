#!/bin/bash
mv /home/cirlab/indriya_upgrade/nohup.out /home/cirlab/indriya_upgrade/nohup.out_$(date +%F-%T.out)
sleep 5
mv /var/log/indriya/indriya.log /var/log/indriya/indriya.log_$(date +%F-%T.out)
sleep 5
cd ~/indriya_upgrade && nohup ./indriya_autostart.py &
sleep 5
curl -X POST http://localhost:5000/reload_jobs
