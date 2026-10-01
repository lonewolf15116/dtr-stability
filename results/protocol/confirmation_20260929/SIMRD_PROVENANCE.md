# simrd provenance for the 29 September batch (checked 2026-10-01)

The batch manifest's simulator_commit field holds the dtr-stability repo commit (4bc152e), because
the laptop's external/simrd folder is a copy without its own .git, so git resolved to the parent repo.
This file replaces that field with a content check.

- Reference: clean checkout of uwsampl/dtr-prototype at eff53cc4804cc7d6246a6e5086861ce2b846f62b (cloud; git status clean).
- Laptop: C:\Users\Mahesh Reddy\Projects\dtr-stability\external\simrd, the DTR_SIMRD used by run_windows.bat.
- All 19 simrd/**/*.py source files: SHA-256 identical (lists below).
- All 9 files in logs/ (8 traces + manifest.json): SHA-256 identical.
- No file under the laptop's simrd/ or logs/ has a modification time after 2026-09-25 22:25 (the newest are .pyc caches),
  i.e. before the batch ran on 29 September.

Conclusion: the files present now are byte-identical to commit eff53cc4, and their modification times predate the
batch. That supports, but does not prove, that the batch used them: timestamps can be preserved or altered, and this is
a retrospective check, not a value recorded at run time. A rerun would not change this; it would only establish
provenance for the new runs.

## Source hashes (identical on both hosts)
```
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  simrd/__init__.py
cf4b4210d7c25a0fe441d08873b4210ae3ea6f4d2afdf0cba6269ffeee9590ef  simrd/heuristic/__init__.py
a6bd57e0079299c3687c2a03560c55533061c2f7c1c41c7af13920cfae2c02d2  simrd/heuristic/ablation.py
8a3f42d559fb92f1f990b4706f47984e205ca078adaae42d264a376a4e3dba9d  simrd/heuristic/dtr.py
07c589eb13573ef2709fa0ca1f38e8e6478a4379d3d5d5fd6ff1bd6f17493b3e  simrd/heuristic/etc.py
d9ea4c833baa52d1bf7e9200423d695099199a1a7fc69eaf3487f46572ba787f  simrd/heuristic/heuristic.py
7748b195352d12bf77f6389364806f3726c0cae6ba51c323dc75674573b68653  simrd/optimization/__init__.py
212c72c4616bec2edf091e7d208d94ef91f2b57ebf110b836c10b637804a4d6f  simrd/optimization/eqclass.py
19f352ef2d4e060b5532562e12d61b41e08d7da6ba9d386518c5ec2fd0d29e65  simrd/optimization/region.py
f42539ea47e59ebd256e45538435485ed01f6dad065d3718216935e8492a9a99  simrd/parse/__init__.py
610a6ae9f08212f46a98853614598b1c74575eda7d72c3001c3bd2e31db38d95  simrd/parse/checkmate.py
889439db51659593642082cdffcbbc2cf06fe182a6c765345272e575f60e0e1f  simrd/parse/graph.py
1b55bf72963ee329b3cfe79653eeec4a586287c915e3d15321bb5a3a7aa6809a  simrd/parse/parse.py
c332aafc9d2586f0e808ad258aebe34ef1054bae1edff7ce994d8432281b5765  simrd/runtime/__init__.py
e3440021e19e593298b882b46bde5701a7e144d120419249ef9051aabc6922f6  simrd/runtime/runtime.py
370fd8748adf884b411007244db84523fe980517fcb091e462ada94b6c83565e  simrd/runtime/v1.py
80f31114300bf42be4ab71d665f1bc6991c0a32e4223c6462fc0654fbc93ae84  simrd/runtime/v2.py
1c843f9a2719d1c2c20af95e01f775efee5cc44d408e7fbf279cb8660ec9bb74  simrd/telemetry.py
538efb20bdea698ac3c3a915374798f5c95406e0a65d0d013f2c6781997005e2  simrd/tensor.py
```
## Trace hashes (identical on both hosts)
```
439a2b9a7a080faabfbc2c751d66d2838664882e3b603196d1c2f41ac64ee9df  inceptionv4-64-10000000000.0-2020-10-1-10-55-0-default.log
f17c569c87bcd1368cc1d1eb0ad79cc75ac8eea0985755c6cd437d7faff2a31f  lstm-128-11000000000.0-2020-10-1-16-38-52-default.log
9b974993063a9fff7b32b25af5b1dd7960d3e60a6814a7829ed1ae6c2a0d7fa4  manifest.json
38c94cada99aca654ad9589d99eabc2267a51835593b598085f9f8221a7bacaf  resnet32-56-9000000000.0-2020-10-1-13-3-30-default.log
cdcac0e9f4af95ccf30cacb28f9edcc2f194c31653946f9ddde424f926fcb7d1  transformer-10-8000000000.0-2020-10-1-10-56-5-default.log
4ec05ef5a1bd81a0c47a4eb13fa708e015333c2568c26f8cdfa1e8c9f2de5902  treelstm-6-8000000000.0-2020-10-1-12-54-1-default.log
4d9e8bd06f6b76c894dfbef4743f714177665dee9e883aa245c2770fe48e45de  tv_densenet121-84-10000000000.0-2020-10-1-13-41-18-default.log
cf985d2ca964c89988e931ee1978302deb22ffb17bc518da0f39344b66d23476  unet-6-8000000000.0-2020-10-1-10-57-18-default.log
0947d26a48e6677b6d437b1415245aa7bb1c638207e8420e4a1e52a094137120  unroll_gan-512-10000000000.0-2020-10-1-18-43-42-default.log
```
