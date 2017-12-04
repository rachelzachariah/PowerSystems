#To run this code, do the following:
#python random_eqs.py -n [NUMBER OF BUSES] -iters [NUMBER OF ITERATIONS] -edges [EDGES]
#
#To specify edges, it should be a string of the form "ab,cd,eg,...,jk" where each variable here is a number.
#For example, the complete graph on 3 buses is "01,12,02", as we assume it's undirected.
#If you don't use the -edges command, it will default to a complete graph.
#
#Example : python find_eqs.py -n 4 -iters 1000 -edges "01,12,23,03 -target 12"
#This generates a graph on 4 buses with edges (0,1), (1,2), (2,3), (0,3)
#It then generates 1000 random equations and tries to find instances with 12 real solutions
#
#

import numpy as np
import subprocess
import sys
import argparse


#Input: Matrix A describing the adjacency of the graph.
#Output: A string corresponding to random equations in this system.
#The format of the string is amenable to PHC.
def random_pq_eqs(A):
	n = A.shape[0]
	x_names = ['x'+str(i) for i in range(1,n)]
	y_names = ['y'+str(i) for i in range(1,n)]

	B = np.zeros([n,n])
	t = 0
	for i in range(n):
		for j in range(i,n):
			if A[i,j] != 0:
				### This distribution controls the susceptances ###
				B[i,j] = B[j,i] = np.random.normal(0,1)
	x = [str(1)]+x_names
	y = [str(0)]+y_names

	f = []
	h = []
	for i in range(1,n):
		### This distribution controls the P and Q variables ###
		p_eq = str(0)
		h_eq = x[i]+"^2+"+y[i]+"^2-1"
		for j in range(n):
			if A[i,j] != 0:
				p_eq += "+("+str(B[i,j])+")*("+x[j]+"*"+y[i]+"-"+x[i]+"*"+y[j]+")"
		f.append(p_eq)
		h.append(h_eq)
	eqs = f+h
	return eqs

#Writes eqs to the file specified by filename.
def write_equations(eqs,filename):
	disp = str(len(eqs))+'\n'
	for coeff in eqs:
		str_coeff = str(coeff)
		disp = disp+str_coeff.replace(' ','') + ';\n'
	f = open(filename+'_eqs.txt','w')
	f.write(disp)
	f.close()

#This generates iters many random equations according to the n-bus system
#with adjacency matrix A.
#tol is the tolerance for certifying a number is real (ie. imaginary part < tol)
#If the number of real solutions equals the target, it prints the equation to the screen
def eq_loop(A,iters,tol,n,target):
	seed = np.random.randint(0,100000)
	prog_checker = iters/10
	instances_found = 0

	for i in range(iters):
		eqs = random_pq_eqs(A)#Generate random equations
		write_equations(eqs,'temp_'+str(seed)+"_"+str(i))#Write them to a file

		#We now try to solve them using phc
		try:
			subprocess.call(["./phc","-b","temp_"+str(seed)+"_"+str(i)+"_eqs.txt","temp_"+str(seed)+"_"+str(i)+"_roots.txt"])
			subprocess.call(["./phc","-x","temp_"+str(seed)+"_"+str(i)+"_eqs.txt","temp_"+str(seed)+"_"+str(i)+"_eqs.dic"])
		except:
			print "Solving system "+str(i)+" failed"

		number_real = 0

		#We now determine how many real solutions there were
		try:
			#This is the file from PHC recording all kinds of information about the solution set
			f = open("temp_"+str(seed)+"_"+str(i)+"_eqs.dic","r")
			s = f.read()
			sols = eval(s)

			known_keys = ['res','err','multiplicity','time','rco']
			#These are known pieces of data the file contains that aren't useful to us
			
			#We now loop through the solutions and calculate how many are real.
			for sol in sols:
				is_real = True
				for k in sol.keys():
					if k not in known_keys:
						root = sol[k]
						if abs(root.imag) > tol:
							is_real = False
				if is_real:
					number_real += 1
			f.close()

		except:
			print "Could not read file "+str(i)

		#If the number found equals the target
		if number_real == target:
			instances_found += 1
			#We now print the equation
			print "Instance "+str(instances_found)+":"
			for coeff in eqs:
				print str(coeff)
			print ""
			

		#Deleting the text files created	
		try:
			subprocess.call(["rm","-f","temp_"+str(seed)+"_"+str(i)+"_eqs.txt"])
		except:
			print "Error removing temp_"+str(seed)+"_"+str(i)+"_eqs.txt"

		try:
			subprocess.call(["rm","-f","temp_"+str(seed)+"_"+str(i)+"_eqs.dic"])
		except:
			print "Error removing temp_"+str(seed)+"_"+str(i)+"_eqs.dic"

		try:
			subprocess.call(["rm","-f","temp_"+str(seed)+"_"+str(i)+"_roots.txt"])
		except:
			print "Error removing temp_"+str(seed)+"_"+str(i)+"_roots.txt"			

	#Total number of instances found
	print "Instances found: "+str(instances_found)

#Here we take the arguments passed via the command line.
parser = argparse.ArgumentParser()
parser.add_argument('-iters', type=int, dest="iters", default = 1000) #How many graphs to check
parser.add_argument('-tol', type=float, dest="tol", default = 0.0000001) #What tolerance should we use to determine if something is a real solution
parser.add_argument('-n', type=int,dest="n", default=4)#Number of buses
parser.add_argument('-edges', dest="e", type=str, default="")#Edges structure, eg. "01,12,23"
parser.add_argument('-target', dest="t", type=int, default=0)#How many solutions we are looking for

args = vars(parser.parse_args())
iters = args["iters"]
tol = args["tol"]
n = args["n"]
edge_string = args["e"]
target = args["t"]

#We now construct the edges corresponding to the edge string
if len(edge_string) > 0:
	edges = [(int(a[0]),int(a[1])) for a in edge_string.split(",")]
else:
	edges = [(i,j) for i in range(n) for j in range(i+1,n)]

#This creates the adjacency matrix
A = np.zeros([n,n])
for e in edges:
	A[e[0],e[1]] = A[e[1],e[0]] = 1

#This is the main call of the algorithm
eq_loop(A,iters,tol,n,target)

#To change the distribution of the variables, see the commented parts of random_pq_eqs.
#You can change to any of the distributions located at: https://docs.scipy.org/doc/numpy/reference/routines.random.html




