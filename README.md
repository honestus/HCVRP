# Heterogeneous capacitated vehicle routing problem (HCVRP) #

This project is realized for educational purposes and it deals to generate/load instances suitable for HCVRP and to solve them, using the CBC solver or the GLPK one, through the PuLP module.


## Tools and Python packages needed ##
It is written in Python and to run it requires:
* Python 3.x
* [CBC](https://projects.coin-or.org/Cbc)
* [GLPK](https://www.gnu.org/software/glpk)
* [PuLP](https://pythonhosted.org/PuLP)
* Pandas-0.20.x (Python package)
* Numpy (Python package)
* random, time, math, pickle, os and sys (Python default packages)


## Directories ##

* config - contains the configurations files
* data - 60 different initial (VRP) instances
* doc - documentation
* instances - (HCVRP) instances already generated
* problems - HCVRP models defined (and eventually solved) for a given instance
* src - source files


## Usage ##

To execute it, you can insert up to two parameters, the first one indicating the filename to load instances already generated (or the configuration file to generate them), the second one indicating the filename to save the instances and the problems.
If no parameters are used, a new instance is generated using the settings loaded from the configuration file (config.txt), then, after defining a new model for it, it'll be run using the parameters specified in the solver configuration file(solverconf.txt).
To modify the solver or instance parameters, it is necessary to manually change files solverconf.txt or config.txt, inside the directory config.
For what concerns <b><i>solverconf.txt</i></b>, please note that the only available values for <i>solver</i> are 'CBC' or 'GLPK'; then for the <i>relax</i> parameter you've to use 'True'or 'False'; finally, for <i>relaxMethods</i> please list the parameters('mir', 'gomory', 'cover' or 'clique') to use, separated by a comma (e.g. 'mir,gomory').

Examples

* Generate new instances (using the settings written in 'config.txt'), solve the problem and save it on istanze1(.dat) and save the model on istanze1(.prob)
  <br><b><i>python3 SOLVER.py config.txt istanze1 </i></b>

* Load instance(from the file 'instance7.dat'), then solve the problem using the solver settings specified in 'solverconf.txt'
  <br><b><i> python3 SOLVER.py instance7.dat </i></b>
