from instances import *
import pulp as plp
import sys, os

problemSavedPath = path+'/problems/'

def makeStandardStructures(instances=None):
    """ Generates the data structures needed by PuLP for the instances actually in use """
    if instances is None:
        if not actualInstances in globals():
            print ("No instances currently generated")
            return
        else:
            instances = actualInstances
    global vehicles, costs, routes
    vehicles = [i+1 for i in range(instances['vehicles'])] #genero lista di veicoli pari al num di veicoli disponibili per l'istanza
    costs = [instances['V1_cost'],instances['V2_cost']]
    #vehiclesCapacities = {i: (instances['capacity'],instances['costoV1']) if i<=instances['T1Vehicles'] else (instances['capacity']/2,instances['costoV2']) for i in vehicles} #dizionario delle capacità, i primi "instances['T1Vehicles']" elementi avranno capacità e costo pari a quelli del veicolo grande, gli altri uguale a quelli del veicolo piccolo
    routes = [(i,j) for i in range(instances['clients']+1) for j in range(instances['clients']+1)] #lista di coppie indicanti tutte le strade possibili (da ogni nodo i a ogni nodo j)

def setSolverOptions(problem=None, options=None):
    """ Sets the solver to be used and its own settings to solve the HCVRP current problem """

    def getCorrectedValues():
        """ Checks the variables values are actually correct.
        If they aren't, they will be set to default values (solver:'CBC', maxTime:900, utilizzo di cuts: 'False') """
        stdSolver = "CBC"
        stdMaxTime= 900
        stdRelax=False
        stdGLPKRelaxMethod="cuts"
        stdCBCRelaxMethod="mir"
        allowableSolvers=["cbc","glpk"]
        allowableGLPKRelaxMethods = ["cuts","gomory","mir","cover","clique"]

        try: #checks solver name has allowed value
            if str(options["solver"]).lower() not in allowableSolvers: #controllo che il solver in input sia CBC o GLPK
                options["solver"]=stdSolver
        except KeyError:
            options["solver"] = stdSolver

        try: #checks maxTime has allowed value
            options["maxTime"]=round(options["maxTime"])
            if options["maxTime"]<=0:
                options["maxTime"] = stdMaxTime
        except TypeError:
            options["maxTime"] = stdMaxTime
        except KeyError:
            options["maxTime"] = stdMaxTime

        try: #checks relax and relaxMethod have allowed values
            if str(options["relax"]).upper() in ['TRUE',1]:
                options["relax"] = True
            else:
                options["relax"] = stdRelax
            if options["relax"]:
                if options["solver"]=="GLPK":
                    try:
                        if type(options["relaxMethods"]) is str:
                            options["relaxMethods"]=options["relaxMethods"].split(',')
                        options["relaxMethods"]=[str(method).lower().strip() for method in options["relaxMethods"] if str(method).lower().strip() in allowableGLPKRelaxMethods]
                        if len(options["relaxMethods"]) == 0:
                            options["relaxMethods"] = stdGLPKRelaxMethod
                    except KeyError:
                        options["relaxMethods"] = stdGLPKRelaxMethod
                else:
                    try:
                        options["relaxMethods"]=[method+'_cuts' for method in options["relaxMethods"] if method in allowableCBCRelaxMethods]
                        if len(options["relaxMethods"]) == 0:
                            options["relaxMethods"] = stdCBCRelaxMethod
                    except KeyError:
                        options["relaxMethods"] = stdCBCRelaxMethod

        except KeyError:
            options["relax"]=stdRelax

        return options



    if problem is None:
        #if no problem is actually instantiated, generates a new one and sets myProblem to the currently instantiate problem
        if not 'myProblem' in globals():
            print ("No problem actually generated")
            return
        else:
            problem=myProblem
    global solverSettings
    if options is None:
        if not 'solverSettings' in globals():
            options = getCorrectedValues() #if no values for solverSettings, the default ones are used
            solverSettings = options
        else:
            options = solverSettings
    else:
        options = getCorrectedValues()
        solverSettings = options  #update solverSettings with respect to the last execution

    solver = options['solver']
    maxTime = options['maxTime']
    relax = options['relax']

    if solver == 'GLPK':
        settings = ['--tmlim', str(maxTime)]
        if relax:
            for relaxMethod in options['relaxMethods']:
                settings.append('--'+str(relaxMethod))
        problem.setSolver(plp.GLPK(msg=1, options = settings))#  sets GLPK and its parameters as solver
    else:
        problem.setSolver(plp.solvers.PULP_CBC_CMD(msg=1, maxSeconds=maxTime)) #sets CBC and its own parameters

    return problem


def instantiateProblem(instances=None,solverOptions=None):
    """ Defines the current HCVRP problem to be solved and its own constraints in PuLP.
    _param_: solverOptions is a dict containing the solver settings """

    if not "myProblem" in globals() or not "actualInstances" in globals() or not instances is None:
        global myProblem, actualInstances
        #se le istanze su cui definire e risolvere il problema sono diverse dalle ultime già definite:
        #1) assegno ad actualInstances il valore delle istanze in input
        #2) quindi rigenero il problema e le strutture utili per generarlo
        actualInstances = instances
        makeStandardStructures(instances)
        myProblem = plp.LpProblem("HCVRP",plp.LpMinimize) #dichiarazione della funzione obiettivo da minimizzare.

        # dichiarazione delle decision variables e dei vincoli del modello...

        #supply_Pulp corrisponde agli y_ij_k(quindi ai beni da trasportare da i a j) per ogni nodo i e j
        supply_Pulp = [plp.LpVariable.dicts("supply grande" if k==0 else "supply picc",(range(instances['clients']+1),range(instances['clients']+1)),lowBound=0,upBound=instances['capacity']+instances['capacity']/2) for k in range(2)]
        for supply in supply_Pulp:
            for i in supply.keys():
                supply[i][i]=0 #setto a 0 le merci da "portare" da un nodo a se stesso

        #route_Pulp corrisponde agli x_ij_k per ogni nodo i e j, per ogni veicolo k
        #NB: dichiarando lowBound=0 soddisfiamo il vincolo 9!!!
        route_Pulp = [plp.LpVariable.dicts("routes veicolo grande" if k==0 else "routes veicolo piccolo",(range(instances['clients']+1),range(instances['clients']+1)),lowBound=0,upBound=instances['vehicles'],cat='Integer') for k in range(2)]
        for route in route_Pulp:
            for i in route.keys():
                route[i][i]=0 #setto a 0 i cammini da un nodo a se stesso

        #demand_Pulp corrisponde ai b_i_k(quindi indica il n° di beni da assegnare ad i dal veicolo di tipo k),
        # per ogni nodo i.
        #NB: dichiarando lowBound=0 soddisfiamo il vincolo 8!!
        demand_Pulp = [plp.LpVariable.dicts("demand grande" if k==0 else "demand piccolo",(range(instances['clients']+1)),lowBound=0,upBound=instances['capacity'] if k==0 else instances['capacity']/2) for k in range(2)]
        for demand in demand_Pulp:
            demand[0]=0 #setto a 0 la demand del depot


        #vincolo 1
        for k in range(2):
            for j in range(1,instances['clients']+1):
                myProblem += plp.lpSum([route_Pulp[k][i][j] for i in range(instances['clients']+1)]) <= 1

        #vincolo 2
        for k in range(2):
            for j in range(1,instances['clients']+1):
                myProblem += plp.lpSum([route_Pulp[k][i][j] for i in range(instances['clients']+1)]) - plp.lpSum([route_Pulp[k][j][l] for l in range(instances['clients']+1)]) == 0

        #vincolo 3
        myProblem += plp.lpSum([route_Pulp[k][0][j] for j in range(1,instances['clients']+1)])<=instances['T1Vehicles'] if k==0 else plp.lpSum([route_Pulp[k][0][j] for j in range(1,instances['clients']+1)])<=instances['T2Vehicles'] , "vincolo 3"

        #vincolo 4
        for i in range(instances['clients']+1):
            myProblem += plp.lpSum([demand_Pulp[k][i] for k in range(2)])== instances['df']['Demand'][i], "vincolo 4, client %s"%i

        #vincolo 5
        for k in range(2):
            for j in range(1,instances['clients']+1):
                myProblem += plp.lpSum([supply_Pulp[k][i][j] for i in range(instances['clients']+1)]) - plp.lpSum([supply_Pulp[k][j][l] for l in range(instances['clients']+1)]) == demand_Pulp[k][j]

        #vincolo 6
        for (i,j) in routes:
            for k in range(2):
                myProblem += supply_Pulp[k][i][j] <= route_Pulp[k][i][j]*instances['capacity'] if k==0 else supply_Pulp[k][i][j] <= route_Pulp[k][i][j]*instances['capacity']/2, "vincolo 6, arco %s %s, veicolo %s" %(i,j,k)

        #funzione obiettivo
        myProblem+=plp.lpSum([route_Pulp[k][i][j]*instances['distances'][i][j]*costs[k] for (i,j) in routes for k in range(2)]), "objective function"


    #infine aggiorno le impostazioni del solver per la risoluzione del problema
    if solverOptions is None:
        setSolverOptions(myProblem) #se solverOptions è Null, allora utilizzo come impostazioni
                                    #le impostazioni attualmente salvate (come variabile global "solverSettings")
    else:
        setSolverOptions(myProblem,solverOptions) #altrimenti uso quelle in input
    return myProblem


def saveProblem(fileName, problem):
    """ saves the problem in input on file(fileName in input; in directory problems/) """
    fileName=problemSavedPath+fileName
    if os.path.isfile(fileName):
        print("Cannot save the problem using the name chosen. Please use a different name.")
        return False
    tmpFile = open(fileName, 'wb')
    pickle.dump(problem, tmpFile, protocol=3)
    tmpFile.close()
    print ("Problem correctly saved!")


def loadProblem(fileName):
    """ loads the problem from file(fileName in input; in directory problems/) """
    #carica istanze dal file in input, verificando che esista e che il contenuto sia corretto e completo
    if not os.path.isfile(problemSavedPath+fileName):
        if not os.path.isfile(fileName):
            print ("There are no existing files with the name you've inserted. Please be sure you've written"
               " it correctly.")
            return False
    else:
        fileName = problemSavedPath+fileName

    try:
        tmpFile = open(fileName, 'rb')
        problem = pickle.load(tmpFile)
        tmpFile.close()
        return problem
    except:
        print("It's not possible to load the problem from the file. The content is different from the expected one.")
        return False
#reload object from file


def main(solverConfigFile=solverSettingsFile):
    try:
        instancesFile = sys.argv[1]
    except IndexError:
        instancesFile = instancesSettingsFile
    try:
        savingPath = sys.argv[2]
    except IndexError:
        savingPath = ''

    # Genera le istanze "standard" prendendo le impostazioni nel file di configurazione "config.txt".
    # Quindi "genera e risolve il problema per tali istanze, utilizzando come parametri per il solver
    # i valori contenuti nel file di configurazione "solverconf.txt".
    global actualInstances, solverSettings
    tmp=getInstances(instancesFile)
    actualInstances = tmp[0]
    alreadyGenerated = tmp[1]
    if actualInstances is False:
        print('Error generating/loading the instances. Please try again and be sure to use all settings properly in the configuration file.')
        return

    printInstancesValues()
    print("\n\n**************************************\nLoading the settings for the solver ...")
    solverSettings=loadSettings(solverConfigFile,solverFileType)
    if solverSettings is False:
        solverSettings={'solver':'CBC','maxTime':900,'relax':False}
        print('Error loading the solver settings. They have been automatically set to the standard values:\n',solverSettings)
    else:
        print("\nSolver settings correctly loaded.")
    print("\nDefining the problem for the current instances...")

    instantiateProblem(actualInstances,solverSettings)
    solver = solverSettings['solver']
    relax = solverSettings['relax']
    print("Problem correctly defined, having. It's time to solve it, using solver: ", solver,' and relaxing the bound using method: ' + str(solverSettings['relaxMethods']) if solverSettings['relax'] else ', not relaxing the bound')

    start=time.time()
    myProblem.solve()
    solutionTime = time.time()-start
    status = plp.LpStatus[myProblem.status]
    obj = plp.value(myProblem.objective)
    print("\n Solution ended with the following results. \n"
                  +"Tempo utilizzato per la risoluzione: ", solutionTime, "\nStatus: ", status,
                    "; valore funzione obiettivo: ", obj, "\n\n")
    if savingPath!='':
        while str(savingPath).strip()=='':
            savingPath=input("Please insert a name for the file to save.")
        if alreadyGenerated==0:
            print('Saving the current instances...')
            while saveInstances(savingPath+'.dat') is False:
                savingPath=input("")
        print('Saving the current problem...')
        while saveProblem(savingPath+'.prob',myProblem) is False:
            savingPath=input("")


main()
