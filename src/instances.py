import numpy as np
import pandas as pd
import random, time, math, os, sys, pickle

def initParameters():
    """ Init the parameters of the distinct useful paths for instances, solver, configuration etc."""
    global instancesFileType,solverFileType, path, originalDataPath, instancesSettingsFile, solverSettingsFile, instancesSavedPath
    solverFileType=1
    instancesFileType=2
    #path= os.path.dirname(os.path.dirname(os.path.abspath(path=sys.argv[0])))
    pathOld= os.path.dirname(os.getcwd())
    path = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
    print(path)
    originalDataPath=path+"/data/"
    instancesSavedPath=path+"/instances/"
    instancesSettingsFile=path+"/config/config.txt"
    solverSettingsFile=path+"/config/solverconf.txt"


def setInstances(instances):
    """ Updates the instances to currently solve the problem on """
    global actualInstances
    actualInstances=instances


def loadSettings(fileName, fileType):
    """ Loads all the settings needed to solve the problem """
    if not "solverFileType" in globals() or not "instancesFileType" in globals():
        initParameters()

    def isComplete(settings):
        """ Checks that the any settings needed for execution is not missing from the ones currently loaded """
        if fileType==instancesFileType:
            neededVariables = ['clients','min_avg_req','max_avg_req','capacity','V1_percent','min_num_vehicles',
                         'max_num_vehicles','var', 'min_req','V1_cost','V2_cost']
        elif fileType==solverFileType:
            neededVariables = ['solver', 'maxTime']
        else:
            return False

        if set(settings.keys())>=set(neededVariables):
            #se settings contiene(come chiavi) ALMENO tutte le variabili necessarie(quelle di neededVariables)...
            utilSettings = {k: settings[k] for k in neededVariables}
            if '' not in utilSettings.values():
            # e nessun valore associato alle chiavi è '', allora restituisce True
                return True
        return False #altrimenti restituisce False

    def isValid(settings):
        """ Checks that the any settings currently loaded is semantically correct and has feasible values """
        if fileType==instancesFileType:
            clients = settings['clients']
            minAvgReq = settings['min_avg_req']
            maxAvgReq = settings['max_avg_req']
            capacity = settings['capacity']
            V1Percent = settings['V1_percent']
            minNumVehicles = settings['min_num_vehicles']
            maxNumVehicles = settings['max_num_vehicles']
            var = settings['var']
            minReq = settings['min_req']
            return (type(clients) is int and 0 < clients <= 100 and 0 < minAvgReq <= maxAvgReq <= 1.5 and type(capacity) is int and capacity > 0 and 0 <= V1Percent <= 1 and 1<= minNumVehicles <= maxNumVehicles and var > 0 and 0 < minReq <= 1)
        elif fileType==solverFileType:
            solver = settings['solver']
            maxTime = settings['maxTime']
            return str(solver).upper()=='GLPK' or str(solver).upper()=='CBC' and type(maxTime) is int and maxTime > 0
        else:
            return False


    #dato un file in input, restituisce un dizionario avente un insieme di chiavi-valore
    settings = {}
    utilSettings = {}
    try:
        f = open (fileName,"r")
    except FileNotFoundError:
        fileName = path+"/config/"+str(fileName)
    except IsADirectoryError:
        if fileType==instancesFileType:
            fileName = str(fileName)+"/"+instancesFileName
        elif fileType==solverFileType:
            fileName = str(fileName)+"/"+solverFileName
    try:
        f = open(fileName,"r")
    except FileNotFoundError:
        print("Ooops... Configuration file not found. Please make sure you've inserted the file name correctly")
        return False
    config = f.readlines()   #inserisce nel vettore config un elemento per ogni riga
    for conf in config:
        conf = conf.split("#")[0]    #eliminiamo i commenti finali del file
        try:
            settings[conf.split(": ")[0]] = int(conf.split(": ")[1]) #inserisco nel dizionario le coppie chiave-valore per ogni impostazione
        except ValueError:
            try:
                settings[conf.split(": ")[0]] = float(conf.split(": ")[1])
            except ValueError:
                settings[conf.split(": ")[0]] = conf.split(": ")[1].strip()
        except IndexError: #se ci sono righe vuote o "mal strutturate" nel file, salta quelle linee
            continue
    f.close()

    try:
        if isComplete(settings):
            if isValid(settings):
                return settings
            print ("Ops. Some data has incorrect value for the settings in input. Please adjust it and try again")
            return False
        else:
            print ("It's not possible to load the data from the file. Some value is missing.")
            return False
    except ValueError as v:
        print (str(v))
        return False



def chooseFile():
    """ Chooses a random file(between the 60 currently in data/ folder) to load the instances from """
    global scelta
    scelta=0
    while(scelta<1 or scelta>60):
        try:
            scelta = int(input("Select file (using a number between 1 and 60): "))
        except ValueError:
            print("Uncorrect input. Please try again.")


def caricaDataframe(fileName='random'):
    """ Loads an instances file(whose name is in input) into a pandas DataFrame and removes all the useless features """
    cols = ["stopNR", "X", "Y", "TW1", "TW2", "TW3", "TW4", "Demand", "Time", "Del"]
    colsToRemove=["stopNR", "TW1", "TW2", "TW3", "TW4", "Demand", "Time", "Del"]
    #scegliFile()
    chosenFile = fileName
    if chosenFile=='random':
        chosenFile=str(random.randrange(1,60)) + "G3.DAT"
    elif not chosenFile.endswith('G3.DAT'):
        chosenFile += "G3.DAT"
    try:
        standardDf = pd.read_fwf(originalDataPath+str(chosenFile),names=cols)
        return standardDf.drop(colsToRemove,axis=1)
    except FileNotFoundError:
        print("Instances File chosen Not found")
        raise


def getRandomClients(nOfClients,dataframe=None):
    """ Starting from dataframe, extracts a sample(dataframe) by randomly taking nOfClients(in input) clients from the starting ones """
    if dataframe is None:
        if not 'instancesDf' in globals():
            raise DataframeError('No dataframes actually in use')
            return
        else:
            dataframe=instancesDf
    clientsIndexes = [0]
    if not isinstance(dataframe,pd.core.frame.DataFrame):
        dataframe=caricaDataframe()

    clientsIndexes.extend(random.sample(range(1,len(dataframe)),nOfClients))
    dataframe=dataframe.iloc[sorted(clientsIndexes)]
    dataframe.index=range(nOfClients+1)
    return dataframe


def distances_matrix(dataframe=None):
    """ Starting from a dataframe(in input) having x and y features (for each client),
    generates a distance_matrix for the clients """
    if dataframe is None:
        if not 'instancesDf' in globals():
            raise DataframeError('No dataframes actually in use')
            return
        else:
            dataframe=instancesDf
    distances = [None] * len(dataframe) #crea un vettore di lunghezza pari al numero di nodi

    for i in dataframe.index:
        distances[i] = [0] * len(dataframe) #crea a ogni ciclo un vettore all'interno del vettore distances
        for j in range(i+1,len(dataframe)):
            XDiff = dataframe.X[i] - dataframe.X[j]
            YDiff = dataframe.Y[i] - dataframe.Y[j]
            distances[i][j] = math.hypot(XDiff,YDiff)

    for i in dataframe.index:
        for j in range(i+1,len(dataframe)):
            if(random.randrange(0,9)>2):
                s = 10 #scostamento massimo 10% in circa 7 su 10
            else:
                s = 30 #scostamento massimo 30% in circa 3 su 10
            scost = distances[i][j]/s #scostamento massimo
            distances[j][i] = random.uniform((distances[i][j])-scost, (distances[i][j])+scost)

    return distances


def generateDemands(avgRequest,minimumRequest,maximumRequest,varianza,nOfClients=100):
    """ Starting from nOfClients and avgRequest(of each client), allocates a demand d to each client
    (minimumRequest<=d<=maximumRequest) in such a way that the total demand is equal to: nOfClients * avgRequest.
    Please note that maximumRequest<= V1 capacity + V2 capacity
    (ie: a client cannot be served from more than two vehicles and from more than a vehicle of each type,
    thus its max request mustn't be higher than the sum of V1 and V2 capacity) """
    minDemand = -1
    maxDemand = maximumRequest
    generatedDemands = 0
    totalDemand = nOfClients * avgRequest
    tolerance = 1000
    start = time.time()
    print ("Generating distinct demands for any client...")
    while(minDemand<minimumRequest or maxDemand>maximumRequest or abs(generatedDemands-totalDemand)>(totalDemand/tolerance)):
        #richiesta di un client non può essere minore di minimumRequest o maggiore della somma della capacità dei veicoli
        #d = np.random.dirichlet(np.ones(nOfClients), size=1)[0]
        demands = np.random.normal(avgRequest,scale=varianza*avgRequest,size=nOfClients)
        #tempDemands = list(map(lambda x: x*totalDemand, d))
        minDemand=min(demands)
        maxDemand=max(demands)
        generatedDemands = sum(demands)
        if tolerance==1000 and time.time()-start>60:
            print("The generation of the demands is keeping too much time, model relaxed...")
            tolerance = 500
        elif tolerance==500 and time.time()-start>120:
            tolerance = 200
        elif time.time()-start>180:
            print("The generation of the demands is keeping too much time, trying again relaxing the variance...")
            varianza=varianza*.8
            tolerance=1000
            start = time.time()

    finalDemands = list([0])
    finalDemands.extend(demands)
    print("Clients demands generated correctly...")
    return finalDemands
    #totalDemand = sum(demands)




def generateNumVehicles(minimum,maximum,t1Percent=0.5):
    """ Random chooses the number V of total vehicles (minimum<=V<=maximum) and returns V,
    the number V1 of largest vehicles (as V*t1Percent) and the number V2 of smallest vehicles (V - V1).
    Please note that the minimum in input MUST BE higher than the number of NEEDED
    vehicles(given by getMinNumberOfVehicles()) to satisfy the clients demand."""
    numVehicles = math.ceil(random.uniform(minimum,maximum+1))
    T1Vehicles = math.ceil (numVehicles * t1Percent)
    T2Vehicles = numVehicles - T1Vehicles
    return numVehicles,T1Vehicles,T2Vehicles



def getMinNumberOfVehicles(totalRequests, t1Capacity, t1Percent):
    """ Given (in input) the total clients demand, the V1 vehicles capacity (and thus the V2 one, too)
    and the percentage of V1 vehicles (ie: n° of V1_Vehicles / n° of total Vehicles),
    gives the minimum estimated number of vehicles to handle the total demand """
    avgCapacity = t1Percent * t1Capacity + (1-t1Percent) * (t1Capacity/2)
    return math.ceil(totalRequests / avgCapacity)



# A partire da: capacità minima e massima per il veicolo grande, e dalla percentuale di veicoli grandi rispetto
# ai veicoli totali(t1Percent), genera un intero(tra minCapacity e maxCapacity) che indicherà la capacità
# dei veicoli grandi.
# Quindi sceglie la richiesta media di ogni client che si aggirerà tra l'1% ed il 5% (NB: RICHIESTA MEDIA! UN CLIENT
# PUÒ COMUNQUE RICHIEDERE MOLTO MENO O MOLTO PIÙ!(fino a CapacitàV1+CapacitàV2))
# Infine calcola il numero minimo di veicoli necessari per soddisfare i client, e in base a tale numero minimo
# sceglie quanti veicoli "generare", tra un minimo(che sarà il n°minimo necessario di veicoli, incrementato di un 20%)
#ed un massimo(il doppio rispetto al minimo necessario)
def generateInstances(settings=None): #,minAvgRequest=5,gap=5,maxAvgRequest=20):
    """ Starting from the settings in input, generates the instances to solve the problem on
    More in detail: Starting from minCapacity and maxCapacity for V1(largest vehicle), and from the percentage of V1
    with respect to the number V of vehicles, generates an integer that states the V1 capacity.
    Then randomly generates the clients different requests (the higher the variance in input, the higher the variance of the requests).
    Starting from these data, calculates the min (minV) number of vehicles to satisfy the requests, and finally generates the
    number of vehicles currently in use(randomly from minV*1.2 to minV*2) """
    if settings is None:
        if not 'instancesSettings' in globals():
            raise settingsError('No settings defined to generate new instances')
            return False
        else:
            global instancesSettings
            settings = instancesSettings
    else:
        instancesSettings=settings
    def isValid():
        clients = settings['clients']
        minAvgReq = settings['min_avg_req']
        maxAvgReq = settings['max_avg_req']
        capacity = settings['capacity']
        V1Percent = settings['V1_percent']
        minNumVehicles = settings['min_num_vehicles']
        maxNumVehicles = settings['max_num_vehicles']
        var = settings['var']
        minReq = settings['min_req']
        return (type(clients) is int and 0 < clients <= 100 and 0 < minAvgReq <= maxAvgReq <= 1.5 and type(capacity) is int and capacity > 0 and 0 <= V1Percent <= 1 and 1<= minNumVehicles <= maxNumVehicles and var > 0 and 0 < minReq <= 1)
    if not isValid():
        print ("Cannot generate instances using the settings in input. Some setting has incompatible value")
        return False

    instances = {}
    print ("Generating new instances...")
    #generaCapacitàMax(minCapacity,maxCapacity)
    clients = instances['clients'] = settings['clients']
    capacitàV1 = instances['capacity'] = settings['capacity']
    capacitàV2 = settings['capacity']/2
    t1Percent = settings['V1_percent']
    minAvgRequest = capacitàV1 * settings['min_avg_req']
    maxAvgRequest = capacitàV1 * settings['max_avg_req']
    var = settings['var']
    avgRequest = random.uniform(minAvgRequest,maxAvgRequest)
    demands=generateDemands(avgRequest=avgRequest,minimumRequest=avgRequest*settings['min_req'],maximumRequest=capacitàV1+capacitàV2,varianza=var, nOfClients=clients)
    instancesDf = getRandomClients(clients)

    instancesDf['Demand'] = pd.Series(demands,index=instancesDf.index)
    minNoOfVehicles = getMinNumberOfVehicles(sum(demands),capacitàV1,t1Percent)
    currentVehicles = generateNumVehicles(minimum=minNoOfVehicles*settings['min_num_vehicles'],maximum=minNoOfVehicles*settings['max_num_vehicles'],t1Percent=t1Percent)
    numVehicles = currentVehicles[0]
    T1Vehicles = currentVehicles[1]
    T2Vehicles = currentVehicles[2]

    instances['vehicles']=currentVehicles[0]
    instances['T1Vehicles']=currentVehicles[1]
    instances['T2Vehicles']=currentVehicles[2]
    instances['df']=instancesDf
    instances['distances'] = distances_matrix(instancesDf)
    instances['V1_cost'] = settings['V1_cost']
    instances['V2_cost'] = settings['V2_cost']
    print ("Instances generation complete!")
    setInstances(instances)
    return instances


def saveInstances(fileName,instances=None):
    """ saves the current instances in the specified fileName (in "instances/" dir) """
    if instances is None:
        if not "actualInstances" in globals():
            print ("No instances currently generated to save")
            return False
        else:
            instances=actualInstances
    if not fileName.endswith('.dat') or os.path.isfile(instancesSavedPath+fileName):
        print("Cannot save using the name chosen. Please use a name ending by \'.dat\' "
                              "and not already existing for your file to save.")
        return False

    neededVariables = ['clients','capacity','vehicles','T1Vehicles','T2Vehicles', 'distances', 'df', 'V1_cost', 'V2_cost']
    if set(instances.keys())>=set(neededVariables):
        tmpFile = open(instancesSavedPath+fileName, 'wb')
        pickle.dump(instances, tmpFile, protocol=3)
        tmpFile.close()
        print ('Instances correctly saved!')
    else:
        print ("Cannot save the instances in input. One or more values to save are missing.")
        return False


def loadInstances(fileName):
    """ Loads instances from file (fileName in input, from "instances/" dir) and checks that its values are correct and complete """
    if not os.path.isfile(instancesSavedPath+fileName):
        if not os.path.isfile(fileName):
            print ("There are no existing files with the name you've inserted. Please be sure you've written"
               " it correctly.")
            return False
    else:
        fileName = instancesSavedPath+fileName

    try:
        d = pd.read_pickle(path=fileName)
    except:
        print("It's not possible to load the instances from the file. The content is different from the expected one.")
        return False

    neededVariables = ['clients','capacity','vehicles','T1Vehicles','T2Vehicles', 'distances', 'df', 'V1_cost', 'V2_cost']
    if set(d.keys())>=set(neededVariables):
        instances = dict(d)
        setInstances(instances) #aggiorno il valore di "actualInstances"
        return instances

    else:
        print("It's not possible to load the instances from the file. Some value is missing")
        d.close()
        return False


def getInstances(fileName=''):
    """ Returns a dataframe of the instances.
    If fileName is a .txt file, then it will load the instances settings and generate new instances.
    If fileNames is a .dat file, it will load the previously saved instances.
    Otherwise, it returns the actualInstances(the ones currently used, if any) """
    global actualInstances
    if fileName.endswith('.txt'):
        settings = loadSettings(fileName, instancesFileType)
        return generateInstances(settings), 0

    elif fileName.endswith('.dat'):
        return loadInstances(fileName), 1
    else:
        if not "actualInstances" in globals():
            return ""
        return actualInstances


def printInstancesValues(instances=None):
    """ Prints out the variables values of the current instances """
    if instances is None:
        if not "actualInstances" in globals():
            print ("No instances currently generated")
            return
        else:
            instances=actualInstances
    print("These are the current instances generated: \n\n")
    print("N° of clients:" , instances['clients'])
    print("avg Request: " , np.mean(instances['df']['Demand'][1:]))
    print("min Request: ", min(instances['df']['Demand'][1:]))
    print("max Request: ", max(instances['df']['Demand']))
    print("V1 Capacity: " , instances['capacity'])
    print("V2 Capacity: " , instances['capacity']/2)
    print("N° of vehicles: " , instances['vehicles'])
    print("N° of V1 vehicles: " , instances['T1Vehicles'])
    print("N° of V2 vehicles: ", instances['T2Vehicles'], "\n")
    print(instances['df'])


def init():
    """ Validates filePath, loads instancesDf randomly from a file in "data/",
    finally loads current instances settings from 'config.txt' (in "config/") """
    global instancesDf,instancesSettings
    initParameters()
    instancesDf=caricaDataframe()
    instancesSettings = loadSettings(instancesSettingsFile,instancesFileType)

init()
