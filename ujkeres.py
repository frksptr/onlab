import numpy as np

def ujkeres(p1,p2):
    felezo = (p1+p2)/2
    diff = p1-p2
    if diff[0] == 0:
        mmeroleges = 0
    else:
        m = diff[1]/diff[0]
        mmeroleges = -1/m
    iranyvektor = np.array([1,mmeroleges] / np.sqrt(1+mmeroleges**2))
    return {'ujpont': felezo, 'iranyvektor': iranyvektor}

def sortCCW(xArray, yArray):
    cx = np.mean(xArray)
    cy = np.mean(yArray)
    tan = np.arctan2(yArray - cy, xArray - cx)

    s = np.argsort(tan)

    xs = x[s]
    ys = y[s]
    return {'x': xs, 'y': ys}

def getFurthestNeighbors(x, y):
    size = x.size
    a = np.array(x[0], y[0])
    b = np.array(x[size-1], y[size-1])
    maxDist = np.linalg.norm(a-b)
    ind = np.array([1, size-1])
    
    for i in range(1,size - 1):
        a = np.array([x[i], y[i]])
        b = np.array([x[i-1], y[i-1]])
        dist = np.linalg.norm(a - b)
        if(dist > maxDist):
            maxDist = dist
            ind = np.array([i, i-1])
            
    return {'x': x[ind], 'y': y[ind]}

p1 = np.array([0,0.6])
p2 = np.array([0,-0.6])

a = ujkeres(p1,p2)
