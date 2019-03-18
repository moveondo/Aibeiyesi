#!/bin/bash
export PATH=/opt/anaconda3/bin:$PATH

#exec nohup python -u ../core/${1}.py $* >/dev/null 2>nohup.out &
exec nohup python -u ../core/${1}.py $* > nohup_${1}.out 2>&1 &