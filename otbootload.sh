GNU nano 2.7.4                                                   File: otbootload.sh

cp latest/otswtoload.txt otswtoload.txt
for i in $(seq 1 10)
do
 wget -O latest.zip $(cat otswtoload.txt)
 if [ $? -eq 0 ]
      then
      unzip -o latest.zip
      rm -r latest
      mv opentestbed* latest
      supervisorctl start otbox
      break
      fi
 sleep 1
done

supervisorctl start otbox
