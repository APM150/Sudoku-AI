import SudokuBoard
import Variable
import Domain
import Trail
import Constraint
import ConstraintNetwork
import time
import random

class BTSolver:

    # ==================================================================
    # Constructors
    # ==================================================================

    def __init__ ( self, gb, trail, val_sh, var_sh, cc ):
        self.network = ConstraintNetwork.ConstraintNetwork(gb)
        self.hassolution = False
        self.gameboard = gb
        self.trail = trail

        self.varHeuristics = var_sh
        self.valHeuristics = val_sh
        self.cChecks = cc

    # ==================================================================
    # Consistency Checks
    # ==================================================================

    # Basic consistency check, no propagation done
    def assignmentsCheck ( self ):
        for c in self.network.getConstraints():
            if not c.isConsistent():
                return False
        return True

    """
        Part 1 TODO: Implement the Forward Checking Heuristic

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        Note: remember to trail.push variables before you assign them
        Return: a tuple of a dictionary and a bool. The dictionary contains all MODIFIED variables, mapped to their MODIFIED domain.
                The bool is true if assignment is consistent, false otherwise.
    """
    def forwardChecking(self):
        modificationHistory = {}
        for v in self.network.getVariables():
            if not v.isAssigned():
                neighbours = set()
                for neighbour in self.network.getNeighborsOfVariable(v):
                    if neighbour.isAssigned():
                        neighbours.add(neighbour.getAssignment())
                varIsModified = False
                for value in neighbours:
                    if v.domain.contains(value):
                        self.trail.push(v)
                        v.removeValueFromDomain(value)
                        varIsModified = True
                if varIsModified:
                    modificationHistory[v] = v.domain
        return (modificationHistory, self.network.isConsistent())

    # =================================================================
	# Arc Consistency
	# =================================================================
    def arcConsistency( self ):
        result = {}
        assignedVars = []
        for c in self.network.constraints:
            for v in c.vars:
                if v.isAssigned():
                    assignedVars.append(v)
        while len(assignedVars) != 0:
            av = assignedVars.pop(0)
            for neighbor in self.network.getNeighborsOfVariable(av):
                if neighbor.isChangeable and not neighbor.isAssigned() and neighbor.getDomain().contains(av.getAssignment()):
                    self.trail.push(neighbor)
                    neighbor.removeValueFromDomain(av.getAssignment())
                    result[neighbor] = neighbor.domain
                    if neighbor.domain.size() == 1:
                        self.trail.push(neighbor)
                        neighbor.assignValue(neighbor.domain.values[0])
                        assignedVars.append(neighbor)
                        result[neighbor] = neighbor.domain
        return (result, self.network.isConsistent())

    
    """
        Part 2 TODO: Implement both of Norvig's Heuristics

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        (2) If a constraint has only one possible place for a value
            then put the value there.

        Note: remember to trail.push variables before you assign them
        Return: a pair of a dictionary and a bool. The dictionary contains all variables 
		        that were ASSIGNED during the whole NorvigCheck propagation, and mapped to the values that they were assigned.
                The bool is true if assignment is consistent, false otherwise.
    """
    def norvigCheck ( self ):
        self.forwardChecking()
        result = {}
        for unit in self.network.constraints:
            counter = {}
            for var in unit.vars:
                for value in var.domain.values:
                    counter.setdefault(value, 0)
                    counter[value] += 1
            for value in counter:
                if counter[value] == 1:
                    for var in unit.vars:
                        if var.domain.contains(value) and not var.isAssigned():
                            self.trail.push(var)
                            var.assignValue(value)
                            result[var] = value
                            break
        return (result, self.network.isConsistent())



    """
         Optional TODO: Implement your own advanced Constraint Propagation

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournCC ( self ):
        return self.norvigCheck()

    # ==================================================================
    # Variable Selectors
    # ==================================================================

    # Basic variable selector, returns first unassigned variable
    def getfirstUnassignedVariable ( self ):
        for v in self.network.variables:
            if not v.isAssigned():
                return v

        # Everything is assigned
        return None

    """
        Part 1 TODO: Implement the Minimum Remaining Value Heuristic

        Return: The unassigned variable with the smallest domain
    """
    def getMRV ( self ):
        smallestDomain = self.gameboard.N + 1
        varWithSmallestDomain = None
        for v in self.network.variables:
            if not v.isAssigned() and v.size() < smallestDomain:
                smallestDomain = v.size()
                varWithSmallestDomain = v
        return varWithSmallestDomain

    """
        Part 2 TODO: Implement the Minimum Remaining Value Heuristic
                       with Degree Heuristic as a Tie Breaker

        Return: The unassigned variable with the smallest domain and affecting the  most unassigned neighbors.
                If there are multiple variables that have the same smallest domain with the same number of unassigned neighbors, add them to the list of Variables.
                If there is only one variable, return the list of size 1 containing that variable.
    """
    def MRVwithTieBreaker ( self ):
        if self.getMRV() != None:
            smallestDomain = self.getMRV().domain.size()
            varsWithSmallestDomain = []
            for v in self.network.variables:
                if not v.isAssigned() and v.size() == smallestDomain:
                    varsWithSmallestDomain.append(v)
        else:
            return [None]

        if len(varsWithSmallestDomain) == 0 or len(varsWithSmallestDomain) == 1:
            return varsWithSmallestDomain
        else:
            maxInvolvedConstraintNum = 0
            varsWithMaxConsraints = []
            for targetVar in varsWithSmallestDomain:
                num = self.numOfUnassignedNeighbors(targetVar)
                if num > maxInvolvedConstraintNum:
                    maxInvolvedConstraintNum = num
            for targetVar in varsWithSmallestDomain:
                if self.numOfUnassignedNeighbors(targetVar) == maxInvolvedConstraintNum:
                    varsWithMaxConsraints.append(targetVar)
            return varsWithMaxConsraints

    def numOfUnassignedNeighbors(self, var):
        neighbors = self.network.getNeighborsOfVariable(var)
        unassignedNeighbors = 0
        for n in neighbors:
            if not n.isAssigned():
                unassignedNeighbors += 1
        return unassignedNeighbors


    """
         Optional TODO: Implement your own advanced Variable Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVar ( self ):
        return self.MRVwithTieBreaker()[0]

    # ==================================================================
    # Value Selectors
    # ==================================================================

    # Default Value Ordering
    def getValuesInOrder ( self, v ):
        values = v.domain.values
        return sorted( values )

    """
        Part 1 TODO: Implement the Least Constraining Value Heuristic

        The Least constraining value is the one that will knock the least
        values out of it's neighbors domain.

        Return: A list of v's domain sorted by the LCV heuristic
                The LCV is first and the MCV is last
    """
    def getValuesLCVOrder ( self, v ):
        values = {}     # {value: # of ruling out other values}
        neighbors = self.network.getNeighborsOfVariable(v)
        for value in v.domain.values:
            numOfRuleOutValue = 0
            for neighborVar in neighbors:
                neighborDomain = neighborVar.domain.values
                if value in neighborDomain:
                    numOfRuleOutValue += 1
            values.setdefault(value, numOfRuleOutValue)
        return sorted(values, key=lambda x: values[x])



    """
         Optional TODO: Implement your own advanced Value Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVal ( self, v ):
        return self.getValuesLCVOrder(v)

    # ==================================================================
    # Engine Functions
    # ==================================================================

    def solve ( self, time_left=600):
        if time_left <= 60:
            return -1

        start_time = time.time()
        if self.hassolution:
            return 0

        # Variable Selection
        v = self.selectNextVariable()

        # check if the assigment is complete
        if ( v == None ):
            # Success
            self.hassolution = True
            return 0

        # Attempt to assign a value
        for i in self.getNextValues( v ):

            # Store place in trail and push variable's state on trail
            self.trail.placeTrailMarker()
            self.trail.push( v )

            # Assign the value
            v.assignValue( i )

            # Propagate constraints, check consistency, recur
            if self.checkConsistency():
                elapsed_time = time.time() - start_time 
                new_start_time = time_left - elapsed_time
                if self.solve(time_left=new_start_time) == -1:
                    return -1
                
            # If this assignment succeeded, return
            if self.hassolution:
                return 0

            # Otherwise backtrack
            self.trail.undo()
        
        return 0

    def checkConsistency ( self ):
        if self.cChecks == "forwardChecking":
            return self.forwardChecking()[1]

        if self.cChecks == "norvigCheck":
            return self.norvigCheck()[1]

        if self.cChecks == "tournCC":
            return self.getTournCC()

        else:
            return self.assignmentsCheck()

    def selectNextVariable ( self ):
        if self.varHeuristics == "MinimumRemainingValue":
            return self.getMRV()

        if self.varHeuristics == "MRVwithTieBreaker":
            return self.MRVwithTieBreaker()[0]

        if self.varHeuristics == "tournVar":
            return self.getTournVar()

        else:
            return self.getfirstUnassignedVariable()

    def getNextValues ( self, v ):
        if self.valHeuristics == "LeastConstrainingValue":
            return self.getValuesLCVOrder( v )

        if self.valHeuristics == "tournVal":
            return self.getTournVal( v )

        else:
            return self.getValuesInOrder( v )

    def getSolution ( self ):
        return self.network.toSudokuBoard(self.gameboard.p, self.gameboard.q)
