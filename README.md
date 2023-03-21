# nucleation
including CP2K inputs, analysis scripts, and some useful scripts

/gadget/cp2k2dpmd.py

For now, dpdata 0.2.14 has not finished making a compatible adjustment for cp2k version 8.1 and above. What's more, Virial info (need STRESS_TENSOR ON) and dipole/polarizability info (need MOMENT ON, and/or WANNIER_CENTER ON) can not be extracted from CP2k standard output and be translated to the format of DeepMD-kit input by dpdata. Herein a script to address these problems is attainable.
