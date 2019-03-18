#!/usr/bin/env bash
export PATH=/opt/anaconda3/bin:$PATH
NAME=$1
params=${@:1}
echo "启动 $NAME 守护进程"
#echo ${params}
while true
do
  echo "watch $NAME"
  ID=`ps -ef | grep "$NAME" | grep 'python'  | grep -v "grep" | awk '{print $2}'`
  echo $ID
  if [ ! "$ID" ]; then
    echo "IS NULL"
    echo "重启 $NAME 程序"
    exec nohup python -u ../core/$NAME.py $params > nohup.out 2>&1 &
  else
    echo "NOT NULL"
  fi
  sleep 60
done