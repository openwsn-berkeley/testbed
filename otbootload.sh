cp latest/otswtoload.txt otswtoload.txt
read -r url < otswtoload.txt
a=0
z=1
for i in $(seq 1 10)
do
 wget -O latest.zip $url
 if [ $? -eq 0 ]
    then
      unzip -o latest.zip
      rm -r latest
      mv opentestbed* latest
      a=$z
      break
    fi
 sleep 1
done

if [ $a -eq $z ]
then
  echo True >> otswtoload.txt
else
  echo False >> otswtoload.txt
fi
cp otswtoload.txt latest/
supervisorctl start otbox
