import numpy as np

def findCircle(array):
	
r = 1;
p1 = np.array([1, 0]).transpose();
p2 = np.array([0, -1]).transpose();
pi = np.pi;

center = (p1+p2)/2;
diff = p2-p1;

a = np.linalg.norm(diff);
m = np.sqrt(r*r-(a/2)*(a/2));
mtot = r + m;

alpha = np.arctan(diff[1]/diff[0]);
beta = alpha+pi/2;

beta = np.array([alpha+pi/2, -pi/2+alpha]).transpose();

p3 =  np.column_stack((np.cos(beta),np.sin(beta),np.array([1, 1])))
p3 = p3.dot( np.vstack((mtot * np.identity(2), center)) )
