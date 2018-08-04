# Heterogeneous capacitated vehicle routing problem (HCVRP) #

This project is realized for educational purposes and it deals to generate/load instances suitable for HCVRP and to solve them, using the CBC solver or the GLPK one, through the PuLP module.

## Project description and constraints ##
A logistic company has to organize the short-haul distribution of goods from its central depot to a set of customers in the same city/region; this can be represented by a directed graph with a node for the depot and one for each customer, and two directed arcs for each pair of nodes, in both directions, labeled with the distance between the two (which can be different between the two directions due to one-way streets). The company has a given supply of vehicles stationed at the deposit, of two different sizes: the small-size one carrying half of the total maximum amount of goods as the large-size one. However, it is assumed that goods are “flexible” enough so that they can always be arranged in the vehicle provided that their total amount does not exceed the capacity. Each customer requires a certain amount of goods, and has to be serviced by at most one vehicle of each type (and, clearly, at least by one vehicle). The problem is to serve all the customer at minimal total cost, which is (proportional to) the total distance traveled by all the vehicles and to a factor that depends on the type of the vehicle; in particular, the per-km cost of small-size ones is 75% of the cost of large-size ones.

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
* instances - (HCVRP) generated instances (ie: set vehicle V1 capacity, vehicle V2 capacity, n° of vehicles, n° of V1 vehicles, n° of V2 vehicles, n° of clients, request for each client and distance matrix)
* problems - HCVRP models defined (and eventually solved) for a given instance
* src - source files


## Usage ##

To execute it, you can insert up to two parameters, the first one indicating the filename to load instances already generated (or the configuration file to generate them), the second one indicating the filename to save the instances and the problems.
If no parameters are used, a new instance is generated using the settings loaded from the configuration file (<b>config.txt</b>), then, after defining a new model for it, it'll be run using the parameters specified in the solver configuration file (<b>solverconf.txt</b>).
To modify the solver or instance parameters, it is necessary to manually change files solverconf.txt or config.txt, inside the directory config.
For what concerns solverconf.txt, please note that the only available values for <i>solver</i> are 'CBC' or 'GLPK'; then for the <i>relax</i> parameter you've to use 'True'or 'False'; finally, for <i>relaxMethods</i> please list the parameters('mir', 'gomory', 'cover' or 'clique') to use, separated by a comma (e.g. 'mir,gomory').

Examples

* Generate new instances (using the settings written in 'config.txt'), solve the problem and save it on istanze1(.dat) and save the model on istanze1(.prob)
  <br><b><i>python3 SOLVER.py config.txt istanze1 </i></b>

* Load instance(from the file 'instance7.dat'), then solve the problem using the solver settings specified in 'solverconf.txt'
  <br><b><i> python3 SOLVER.py instance7.dat </i></b>
