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

model = AbstractModel()

#set
model.A = Set() # Departure/destination spot
model.B = Set() # Truck type set

#parameter
model.D = Param(model.A,model.A) # Transport Demand between two spot
model.W = Param(model.B) # Truck capacity

#variable
model.N = Var(model.B, model.A, model.A, domain = NonNegativeIntegers) #decision variable for the number of truck type j used between i and i spot
model.V = Var(model.B, model.A, model.A, domain = NonNegativeReals) #decision variable for volume of delivery between two spots
model.NMR = Var(model.B, model.A, model.A, model.A, domain = NonNegativeIntegers) #decision variable for the number of truck type j used between i, j and k spot
model.VMR = Var(model.B, model.A, model.A, domain = NonNegativeReals) #decision variable for volume of delivery between two spots
model.NMR2 = Var(model.B, model.A, model.A, domain = NonNegativeIntegers) #decision variable for the number of truck type j used between i and j spot within milk run
model.OV = Var(model.A, model.A, domain = NonNegativeReals) #over volume to avoid infeasibility
model.UV = Var(model.A, model.A, domain = NonNegativeReals) #under volume to avoid infeasibility

#objective function & constraints
def obj_expression(model):
    return summation(model.N)+summation(model.NMR)+1000*(summation(model.UV)+summation(model.OV))
model.OBJ = Objective(rule=obj_expression,sense=minimize)

def demandbalance(model,a1,a2):
    return sum(model.V[b,a1,a2] for b in model.B)+sum(model.VMR[b,a1,a2] for b in model.B)+model.OV[a1,a2]== model.D[a1,a2] + model.UV[a1,a2]#demand balance for each route
model.DBConstraint = Constraint(model.A,model.A,rule = demandbalance)

def minflowlimit(model,b,a1,a2):
    return model.W[b]*model.N[b,a1,a2]*0.75 <= model.V[b,a1,a2] #lower limit for the balance between number of truck and volume
model.minflowConstraint = Constraint(model.B,model.A,model.A,rule = minflowlimit)

def maxflowlimit(model,b,a1,a2):
    return model.W[b]*model.N[b,a1,a2]*0.95 >= model.V[b,a1,a2] #upper limit for the balance between number of truck and volume
model.maxflowConstraint = Constraint(model.B,model.A,model.A,rule = maxflowlimit)

def minflowlimitMR(model,b,a1,a2):
    return model.W[b]*model.NMR2[b,a1,a2]*0.75 <= model.VMR[b,a1,a2] #lower limit for the balance between number of truck and volume
model.minflowConstraintMR = Constraint(model.B,model.A,model.A,rule = minflowlimitMR)

def maxflowlimitMR(model,b,a1,a2):
    return model.W[b]*model.NMR2[b,a1,a2]*0.95 >= model.VMR[b,a1,a2] #upper limit for the balance between number of truck and volume
model.maxflowConstraintMR = Constraint(model.B,model.A,model.A,rule = maxflowlimitMR)

def define3cityMR(model,b,a1,a2):
    return sum(model.NMR[b,a1,a2,a3] for a3 in model.A) + sum(model.NMR[b,a3,a1,a2] for a3 in model.A) == model.NMR2[b,a1,a2]
model.define3cityMRConstraint = Constraint(model.B, model.A, model.A, rule = define3cityMR)

#load data
instance = model.create_instance("RouteData.dat")
print('Data upload finished')

#Algorithm
opt = SolverFactory('cplex')
solver_manager = SolverManagerFactory('neos')
results = solver_manager.solve(instance, opt=opt)
if (results.solver.status != pyomo.opt.SolverStatus.ok):
    logging.warning('Check solver not ok?')
if (results.solver.termination_condition != pyomo.opt.TerminationCondition.optimal):  
    logging.warning('Check solver optimality?')
print('No. of Truck: ', instance.OBJ())
results.write()
instance.pprint()
 
