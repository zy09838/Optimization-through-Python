from __future__ import division
import pyomo
from pyomo.environ import *
import pandas as pd
import matplotlib.pyplot as plt
import os
import openpyxl
import numpy
import networkx

#mathematical model (abstract)
#for this simplified model, the problem have been investigated into the level of each bus. For the complete model in the future, will only consider bus type level

model = AbstractModel()

#set
model.t = Set() # Time
model.i = Set() # Route
model.j = Set() # Direction
model.k = Set() # Station
model.l = Set() # Bus

#parameter
#model.AD = Param(model.t, model.i, model.j, model.k) # Actual demand for calculation /time slot/route/direction
model.BC = Param(model.l) # Bus capacity/bus
model.AB = Param(model.l) # Bus number/bus
model.AD2 = Param(model.t, model.i, model.j) # Demand used for calculation

#variable
model.R = Var(model.t, model.i, model.j, model.l, domain = NonNegativeReals) # Required capacity/time slot/route/direction/station/bus
model.RB = Var(model.t, model.i, model.j, model.l, domain = Binary) # Required capacity/time slot/route/direction/station/bus
model.S = Var(model.t, model.i, model.j, domain = NonNegativeReals) #Under capacity/time slot/route/direction/bus
model.O = Var(model.t, model.i, model.j, domain = NonNegativeReals) #Over capacity/time slot/route/direction/bus
model.UU = Var(model.t, model.i, model.j, model.l, domain = NonNegativeReals)#Under usage of capacity/time slot/route/direction/bus

#objective function & constraints
def obj_expression(model):
    return summation(model.S)+summation(model.O)+100*summation(model.UU)
model.OBJ = Objective(rule=obj_expression,sense=minimize)

#def generatedemand(model,a,b,c):
#    return max(model.AD[a,b,c,d] for d in model.k)
#model.Test = Param(model.t, model.i, model.j, initialize = generatedemand)

def demandbalance(model,a,b,c):
    return sum(model.R[a,b,c,d] for d in model.l) + model.S[a,b,c] == model.AD2[a,b,c] + model.O[a,b,c] #demand balance/time slot/route/direction
model.DBConstraint = Constraint(model.t, model.i, model.j,rule = demandbalance)

def busselectionupmap(model,a,b,c,d):
    return model.R[a,b,c,d] <= model.RB[a,b,c,d]*model.BC[d] #up bound of bus selection mapping
model.buselectionupConstraint = Constraint(model.t, model.i, model.j, model.l,rule = busselectionupmap)

def busselectionlowmap(model,a,b,c,d):
    return model.R[a,b,c,d] + model.UU[a,b,c,d] >= model.RB[a,b,c,d]*0.4*model.BC[d] #lower bound of bus selection mapping
model.buselectionlowConstraint = Constraint(model.t, model.i, model.j, model.l,rule = busselectionlowmap)

def maxbuslimit(model,a,d):
    return sum(model.RB[a,b,c,d] for b in model.i for c in model.j) <= model.AB[d] #max number of bus per time slot
model.maxbuslimitConstraint = Constraint(model.t, model.l, rule = maxbuslimit)

#load data
instance = model.create_instance("FakeData.dat")
print('Data upload finished')

#Algorithm
if __name__ == '__main__':
    solver = pyomo.opt.SolverFactory('gurobi') #gurobi available as well
    results = solver.solve(instance, tee=True, keepfiles=False)
    if (results.solver.status != pyomo.opt.SolverStatus.ok):
        logging.warning('Check solver not ok?')
    if (results.solver.termination_condition != pyomo.opt.TerminationCondition.optimal):  
        logging.warning('Check solver optimality?')
    print('Demand mismatch: ', instance.OBJ())
    results.write()
    BusCapacityAllocation = getattr(instance,'R')

#Data export
RouteIndex = list()
BusCapacity = list()
for index in BusCapacityAllocation:
    if value(BusCapacityAllocation[index]) > 0:
        RouteIndex.append(index)
        BusCapacity.append(value(BusCapacityAllocation[index]))
BusCapacity = [round(elem,0) for elem in BusCapacity ]
DecisionOutputVariable = dict()
for x in RouteIndex:
	for y in BusCapacity:
		DecisionOutputVariable.update({x:y})
DecisionOutput = pd.DataFrame({'Index Combination': RouteIndex, 'Required Capacity':BusCapacity})
DecisionOutput.to_excel('Output.xlsx', sheet_name = 'Optimization Output',index=False)
