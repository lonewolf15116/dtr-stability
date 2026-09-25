cd /home/claude/stability
for b in 0.05 0.1 0.5 1 2 4; do
  [ -f resnet_ChainCap_b$b.json ] || python3 harness.py resnet "ChainCap@b=$b" --ratios 0.080:0.150:0.001 --out resnet_ChainCap_b$b.json > resnet_ChainCap_b$b.log 2>&1
done
echo DONE > bsweep.done
