import numpy as np

import matplotlib.pyplot as plt

def findCircle(array):

    pi = np.pi;

    x = np.array([])
    y = np.array([])
    M = np.empty((0,3),int)
    b = np.empty((0,1),int)
    with open("keres.txt","r") as file:
        for line in file:
            currentline = line.split(",")
            if (len(currentline) > 1):
                xi = int(currentline[0])
                yi = int(currentline[1])
                M = np.append(M,np.array([[xi, yi, 1]]),axis=0)
                x = np.append(x,xi)
                y = np.append(y,yi)
                b = np.append(b,np.array([[-xi*xi-yi*yi]]),axis=0)

    
    a = np.linalg.lstsq(M,b)[0]
    a1 = -a[0]/2
    a2 = -a[1]/2
    a3 = -np.sqrt(a[2])
    print(a3)
    print(a1)
    print(a2)
    plt.scatter(x.astype(int), y.astype(int))
    plt.scatter(a1,a2,color='red')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.autoscale('True','both','False')

    plt.show()



findCircle([])
