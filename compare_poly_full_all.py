#!/usr/bin/env python


#Make sure that the folder this is located in has a copy of Bertini.
#Also, make sure to create a folder called Data in this folder in order to properly store results.
#
#To run this code, do the following:
#python bertini_solve.py -n [NUMBER OF BUSES] -iters [NUMBER OF ITERATIONS] -edges [EDGES]
#
#To specify edges, it should be a string of the form "a,b:c,d:e,g:...:j,k" where each variable here is a number.
#For example, the complete graph on 3 buses is "0,1:1,2:0,2", as we assume it's undirected.
#If you don't use the -edges command, it will default to a complete graph.
#
#Example : python bertini_solve.py -n 4 -iters 1000 -edges "0,1:1,2:2,3:3,0"
#This generates a graph on 4 buses with edges (0,1), (1,2), (2,3), (0,3)
#It then generates 1000 random equations and tries to find instances with 12 real solutions
#
#The distribution of real solutions is saved in the Data folder as a .txt document.
#Its file name will be "dist_(graph-id)_(timestamp).txt"
#Here graph-id records the edge structure of G.
#The hope is that later we can just merge all results with the same graph-id.
#The timestamp is just so that different runs don't overwrite the file.
#
#If you'd like to use your own graph id, you can do this with the option -g
#

import numpy as np
import subprocess
import sys
import argparse
import time

#Input: Matrix A describing the adjacency of the graph.
#Output: A string corresponding to random equations in this system.
#The format of the string is amenable to Bertini.
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
	n = len(eqs)/2

	disp = 'function '
	for i in range(n):
		if i > 0: disp += ','
		disp += 'f'+str(i+1)
	for i in range(n):
		disp += ',g'+str(i+1)
	disp += ';'+'\n'

	disp += 'variable_group '
	for i in range(n):
		if i > 0: disp += ','
		disp += 'x'+str(i+1)
	for i in range(n):
		disp += ',y'+str(i+1)
	disp += ';'+'\n'+'\n'

	for i in range(n):
		disp += 'f'+str(i+1)+' = '+eqs[i]+';'+'\n'
	for i in range(n):
		disp += 'g'+str(i+1)+' = '+eqs[n+i]+';'+'\n'
	disp += 'END;'

	f = open(filename+'.input','w')
	f.write(disp)
	f.close()

#This generates iters many random equations according to the n-bus system
#with adjacency matrix A.
#tol is the tolerance for certifying a number is real (ie. imaginary part < tol)
#If the number of real solutions equals the target, it prints the equation to the screen
def eq_loop(A,iters,tol,n,graph_id,verbose=False):
	seed = np.random.randint(0,100000)
	freq_count = {}#This dictionary will record how frequently we see each number of real sol
	prog_checker = iters/10#This will be udpated to say what percentage is completed

	for i in range(iters):
		eqs, b = random_pq_eqs(A)#Generate random equations

		# elim_coeff = poly_coeff(b)
		# elim_roots = np.roots(elim_coeff)
		# num_elim_real = 0
		# for root in elim_roots:
		# 	if root.imag < tol:
		# 		num_elim_real += 2

		write_equations(eqs,'temp_'+str(seed)+"_"+str(i))#Write them to a file

		#We now try to solve them using Bertini.
		try:
			subprocess.call(["./bertini","temp_"+str(seed)+"_"+str(i)+".input","temp_"+str(seed)+"_"+str(i)+"_roots.txt"])
		except:
			print "Solving system "+str(i)+" failed"

		#We now determine how many real solutions there were
		try:
			with open('real_finite_solutions','r') as f: #This is the file from Bertini recording all kinds of information about the solution set
				first_line = f.readline()
				number_real = int(first_line.strip())

				num_elim_real = 0	

				with open('finite_solutions','r') as g: #We will use this to find how many times a single variable is real
					finite_sol = g.readlines()
					var_index = n
					num_finite_sol = int(finite_sol[0].strip())
					for jj in range(num_finite_sol):
						y_line = f[(2*n-3)*jj+ n +1]
						y_val = y.strip()
						y_val_split = y_val.split(' ')
						imag_part = float(y_val_split[1])
						if abs(imag_part) <= tol:
							num_elim_real += 1

					sol_tuple = (number_real,num_elim_real)

					if sol_tuple in freq_count.keys():
						freq_count[sol_tuple] += 1
					else:
						freq_count[sol_tuple] = 1						

		except:
			print "Could not read file "+str(i)

		#Deleting the text files created.
		try:
			subprocess.call(["rm","-f","temp_"+str(seed)+"_"+str(i)+".input"])
		except:
			print "Error removing temp_"+str(seed)+"_"+str(i)+".input"		

		#If verbose, we give a progress update every so often.
		if verbose:
			if i%prog_checker == 0:
				sys.stdout.write(str((float(i)/iters)*100)+' percent completed\n')

	#We now print the frequency count to the screen.
	num_roots_found = freq_count.keys()
	#num_roots_found.sort() #We sort from smallest number to largest number of real roots.
	t = time.localtime()
	timestamp = time.strftime('%b-%d-%Y_%H:%M:%S', t)

	with open('Data/compare_'+graph_id+'_'+timestamp,'w') as f:
		for k in num_roots_found:
			f.write(str(k) + ' : ' + str(freq_count[k])+'\n')

#Here we take the arguments passed via the command line.
parser = argparse.ArgumentParser()
parser.add_argument('-iters', type=int, dest="iters", default = 1000) #How many graphs to check
parser.add_argument('-tol', type=float, dest="tol", default = 0.0000001) #What tolerance should we use to determine if something is a real solution
parser.add_argument('-n', type=int,dest="n", default=4)#Number of buses
parser.add_argument('-edges', dest="e", type=str, default="")#Edges structure, eg. "01,12,23"
parser.add_argument('-v',action='store_true', default=False, dest='verbose') #If verbose, it will tell you when it has done 10, 20, ... %
parser.add_argument('-g', dest = "g", type=str, default="")

args = vars(parser.parse_args())
iters = args["iters"]
verbose = args["verbose"]
tol = args["tol"]
n = args["n"]
edge_string = args["e"]
g = args["g"]

#We now construct the edges corresponding to the edge string
if len(edge_string) > 0:
	edges = [(int(b.split(',')[0]),int(b.split(',')[1])) for b in edge_string.split(':')]
	if len(g) == 0:
		graph_id = ''+edge_string+''
	else:
		graph_id = g
else:
	edges = [(i,j) for i in range(n) for j in range(i+1,n)]
	if len(g) == 0:
		graph_id = 'K'+str(n)
	else:
		graph_id = g

#This creates the adjacency matrix
A = np.zeros([n,n])
for e in edges:
	A[e[0],e[1]] = A[e[1],e[0]] = 1

#This is the main call of the algorithm
eq_loop(A,iters,tol,n,graph_id,verbose=verbose)
