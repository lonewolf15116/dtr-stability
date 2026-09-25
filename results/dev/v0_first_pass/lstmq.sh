cd /home/claude/stability
while [ ! -f bsweep.done ]; do sleep 10; done
for h in ChainCap TieAware TwoPhase; do
  python3 harness.py lstm $h --ratios 0.266,0.265,0.264,0.262 --out lstm_$h.json > lstm_$h.log 2>&1
done
echo DONE > lstmq.done
