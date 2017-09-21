import numpy as np
import subprocess
import sys
import argparse

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

def write_equations(eqs,filename):
	disp = str(len(eqs))+'\n'
	for coeff in eqs:
		str_coeff = str(coeff)
		disp = disp+str_coeff.replace(' ','') + ';\n'
	f = open(filename+'_eqs.txt','w')
	f.write(disp)
	f.close()


def eq_loop(A,iters,tol,n,verbose=False):
	seed = np.random.randint(0,100000)
	freq_count = {}
	prog_checker = iters/10
	for i in range(iters):
		eqs = random_pq_eqs(A)
		write_equations(eqs,'temp_'+str(seed)+"_"+str(i))


		try:
			subprocess.call(["./phc","-b","temp_"+str(seed)+"_"+str(i)+"_eqs.txt","temp_"+str(seed)+"_"+str(i)+"_roots.txt"])
			subprocess.call(["./phc","-x","temp_"+str(seed)+"_"+str(i)+"_eqs.txt","temp_"+str(seed)+"_"+str(i)+"_eqs.dic"])
		except:
			print "Solving system "+str(i)+" failed"

		number_real = 0

		try:
			f = open("temp_"+str(seed)+"_"+str(i)+"_eqs.dic","r")
			s = f.read()
			sols = eval(s)
			known_keys = ['res','err','multiplicity','time','rco']
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
			if number_real%2 ==0:
				if number_real in freq_count.keys():
					freq_count[number_real] += 1
				else:
					freq_count[number_real] = 1
			else:
				print "File "+str(i)+" failed, odd number of solutions detected"
		except:
			print "Could not read file "+str(i)

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


	num_roots_found = freq_count.keys()
	num_roots_found.sort() #We sort from smallest number to largest number of real roots
	print ""
	print "Roots found:"
	for k in num_roots_found:
		print str(k) + ' : ' + str(freq_count[k])

parser = argparse.ArgumentParser()
parser.add_argument('-iters', type=int, dest="iters", default = 1000) #How many graphs to check
parser.add_argument('-tol', type=float, dest="tol", default = 0.0000001) #What tolerance should we use to determine if something is a real solution
parser.add_argument('-v',action='store_true', default=False, dest='verbose') #If verbose, it will tell you when it has done 10, 20, ... %
parser.add_argument('-n', type=int,dest="n", default=4)
parser.add_argument('-edges', dest="e", type=str, default="")

args = vars(parser.parse_args())
iters = args["iters"]
verbose = args["verbose"]
tol = args["tol"]
n = args["n"]
edge_string = args["e"]
if len(edge_string) > 0:
	edges = [(int(a[0]),int(a[1])) for a in edge_string.split(",")]
else:
	edges = [(i,j) for i in range(n) for j in range(i+1,n)]


#This creates the adjacency matrix
A = np.zeros([n,n])
for e in edges:
	A[e[0],e[1]] = A[e[1],e[0]] = 1
print A

#This is the main call of the algorithm
eq_loop(A,iters,tol,n,verbose=verbose)

#To change the distribution of the variables, see the commented parts of random_pq_eqs.
#You can change to any of the distributions located at: https://docs.scipy.org/doc/numpy/reference/routines.random.html




