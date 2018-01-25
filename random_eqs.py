#To run this code, do the following:
#python random_eqs.py -n [NUMBER OF BUSES] -iters [NUMBER OF ITERATIONS] -edges [EDGES]
#
#To specify edges, it should be a string of the form "ab,cd,eg,...,jk" where each variable here is a number.
#For example, the complete graph on 3 buses is "01,12,02", as we assume it's undirected.
#If you don't use the -edges command, it will default to a complete graph.
#
#Example 1: python random_eqs.py -n 4 -iters 1000
#This will generate 1000 complete 4 bus graphs with normal random edge weights
#It will then print out the distribution of real solutions.
#
#Examples 2: python random_eqs.py -n 4 -iters 1000 -edges "01,12,23,03"
#This generates a graph on 4 buses with edges (0,1), (1,2), (2,3), (0,3)
#
#

import numpy as np
import subprocess
import sys
import argparse

#Input: Matrix A describing the adjacency of the graph.
#Output: A string corresponding to random equations in this system.
#The format of the string is amenable to PHC.
def random_pq_eqs(A,mu,var):
	n = A.shape[0]
	x_names = ['x'+str(i) for i in range(1,n)]
	y_names = ['y'+str(i) for i in range(1,n)]

	B = np.zeros([n,n])
	t = 0
	for i in range(n):
		for j in range(i,n):
			if A[i,j] != 0:
				### This distribution controls the susceptances ###
				B[i,j] = B[j,i] = np.random.normal(mu,var)
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
#verbose indicates that it will tell you what percentage is done
#This method prints the distribution of real solutions to the screen.
def eq_loop(A,iters,tol,n,verbose=False,mu,var):
	seed = np.random.randint(0,100000)#Random seed
	freq_count = {}#This dictionary will record how frequently we see each number of real sol
	prog_checker = iters/10#This will be udpated to say what percentage is completed
	for i in range(iters):
		eqs = random_pq_eqs(A,mu,var) #Generate random equations
		write_equations(eqs,'temp_'+str(seed)+"_"+str(i)) #Write them to a file

		#We now try to solve them using phc
		try:
			subprocess.call(["./phc","-b","temp_"+str(seed)+"_"+str(i)+"_eqs.txt","temp_"+str(seed)+"_"+str(i)+"_roots.txt"])
			subprocess.call(["./phc","-x","temp_"+str(seed)+"_"+str(i)+"_eqs.txt","temp_"+str(seed)+"_"+str(i)+"_eqs.dic"])
		except:
			print "Solving system "+str(i)+" failed" #If something goes wrong

		number_real = 0

		#We now determine how many real solutions there were
		try:
			#This is the file from PHC recording all kinds of information about the solution set
			f = open("temp_"+str(seed)+"_"+str(i)+"_eqs.dic","r")
			s = f.read()
			sols = eval(s)
			known_keys = ['res','err','multiplicity','time','rco']#These are known pieces of data the file contains that aren't useful to us
			
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

			#We update our frequency count
			if number_real%2 ==0:
				if number_real in freq_count.keys():
					freq_count[number_real] += 1
				else:
					freq_count[number_real] = 1
			else:
				print "File "+str(i)+" failed, odd number of solutions detected"
		except:
			print "Could not read file "+str(i)


		#We now delete all the text files created
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


		#If verbose, we give a progress update every so often
		if verbose:
			if i%prog_checker == 0:
				sys.stdout.write(str((float(i)/iters)*100)+' percent completed\n')


	#We now print the frequency count to the screen.
	num_roots_found = freq_count.keys()
	num_roots_found.sort() #We sort from smallest number to largest number of real roots
	print ""
	print "Roots found:"
	for k in num_roots_found:
		print str(k) + ' : ' + str(freq_count[k])


#Here we take the arguments passed via the command line.
parser = argparse.ArgumentParser()
parser.add_argument('-iters', type=int, dest="iters", default = 1000) #How many graphs to check
parser.add_argument('-tol', type=float, dest="tol", default = 0.0000001) #What tolerance should we use to determine if something is a real solution
parser.add_argument('-v',action='store_true', default=False, dest='verbose') #If verbose, it will tell you when it has done 10, 20, ... %
parser.add_argument('-n', type=int,dest="n", default=4)#Number of buses
parser.add_argument('-edges', dest="e", type=str, default="")#Edge structure, eg. "01,12,23" gives the complete 3-bus
parser.add_argument('-mu', dest="mu", type=int, default=0)#The mean of the random edges
parser.add_argument('-var', dest="var", type=float, default=1.0)#The variance of the random edges

args = vars(parser.parse_args())
iters = args["iters"]
verbose = args["verbose"]
tol = args["tol"]
n = args["n"]
edge_string = args["e"]
mu = args["mu"]
var = args["var"]

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
eq_loop(A,iters,tol,n,verbose=verbose,mu,var)

#To change the distribution of the variables, see the commented parts of random_pq_eqs.
#You can change to any of the distributions located at: https://docs.scipy.org/doc/numpy/reference/routines.random.html




