NAME=aiBysModel
echo $NAME
P_ID=`ps -ef | grep "$NAME" | grep 'python'  | grep -v "grep" | awk '{print $2}'`
W_ID=`ps -ef | grep "$NAME" | grep 'watchdog'  | grep -v "grep" | awk '{print $2}'`
echo P_ID is $P_ID
echo W_ID is $W_ID
echo "---------------"
for pid in $P_ID
do
kill -9 $pid
echo "killed $pid"
done

for wid in $W_ID
do
kill -9 $wid
echo "killed $wid"
done