printf ("     +-----------------------------------------------+\n")
printf ("     |    Processing Tools for KAPAO Data Products   |\n")
printf ("     |       Joseph Long, Pomona College, 2013       |\n")
printf ("     +-----------------------------------------------+\n")
printf ("\n")
pyexecute("aotools$addpath.py",verbose=no)
pyexecute("aotools$aoavgcube.py",verbose=no)
pyexecute("aotools$cubestack.py",verbose=no)
pyexecute("aotools$cubetoframes.py",verbose=no)
pyexecute("aotools$findbright.py",verbose=no)
pyexecute("aotools$strehlframe.py",verbose=no)
pyexecute("aotools$strehlcube.py",verbose=no)
pyexecute("aotools$pngtofits.py",verbose=no)
package aotools
