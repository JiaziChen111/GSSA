# -*- coding: utf-8 -*-
"""
Created on Fri Sep 08 12:53:03 2017
@author: Daryl Larsen
"""

'''
This program implements the Generalized Stochastic Simulation Algorthim from 
Judd, Maliar and Mailar (2011) "Numerically stable and accurate stochastic 
simulation approaches for solving dynamic economic models", Quantitative
Economics vol. 2, pp. 173-210.
'''
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

from LinApp_FindSS import LinApp_FindSS


'''
We test the algorithm with a simple DSGE model with endogenous labor.
'''

def Modeldefs(Xp, X, Z, params):
    '''
    This function takes vectors of endogenous and exogenous state variables
    along with a vector of 'jump' variables and returns explicitly defined
    values for consumption, gdp, wages, real interest rates, and transfers
    
    Inputs are:
        Xp: value of capital in next period
        X: value of capital this period
        Y: value of labor this period
        Z: value of productivity this period
        params: list of parameter values
    
    Output are:
        Y: GDP
        w: wage rate
        r: rental rate on capital
        T: transfer payments
        c: consumption
        i: investment
        u: utiity
    '''
    
    # unpack input vectors
    kp = Xp
    k = X
    z = Z
    
    # unpack params
    [alpha, beta, gamma, delta, chi, theta, tau, rho, sigma] = params
    
    # find definintion values
    Y = k**alpha*(np.exp(z))**(1-alpha)
    r = alpha*Y/k
    w = (1-alpha)*Y
    T = tau*(w + (r - delta)*k)
    c = (1-tau)*(w + (r-delta)*k) + k + T - kp 
    u = c**(1-gamma)/(1-gamma)
    i = Y - c
    return Y, w, r, T, c, i, u


def Modeldyn(theta0, params):
    '''
    This function takes vectors of endogenous and exogenous state variables
    along with a vector of 'jump' variables and returns values from the
    characterizing Euler equations.
    
    Inputs are:
        theta: a vector containng (Xpp, Xp, X, Yp, Y, Zp, Z) where:
            Xpp: value of capital in two periods
            Xp: value of capital in next period
            X: value of capital this period
            Zp: value of productivity in next period
            Z: value of productivity this period
        params: list of parameter values
    
    Output are:
        Euler: a vector of Euler equations written so that they are zero at the
            steady state values of X, Y & Z.  This is a 2x1 numpy array. 
    '''
    
    # unpack theat0
    (Xpp, Xp, X, Zp, Z) = theta0
    
    # unpack params
    [alpha, beta, gamma, delta, chi, theta, tau, rho, sigma] = params
    
    # find definitions for now and next period

    Y, w, r, T, c, i, u = Modeldefs(Xp, X, Z, params)
    Yp, wp, rp, Tp, cp, ip, up = Modeldefs(Xpp, Xp, Zp, params)
    
    # Evaluate Euler equations
    E1 = (c**(-gamma)*(1-tau)*w) / (chi) - 1
    E2 = (c**(-gamma)) / (beta*cp**(-gamma)*(1 + (1-tau)*(rp - delta))) - 1
    
    return np.array([E1])
    #return np.array([E1, E2])

def poly1(Xin, XYparams):
    '''
    Includes polynomial terms up to order 'pord' for each element and quadratic 
    cross terms  One observation (row) at a time
    '''
    nX = nx + nz
    Xbasis = np.ones((1, 1))
    # generate polynomial terms for each element
    for i in range(1, pord):
        Xbasis = np.append(Xbasis, Xin**i)
    # generate cross terms
    for i in range (0, nX):
        for j in range(i+1, nX):
            temp = Xin[i]*Xin[j]
            Xbasis = np.append(Xbasis, temp)
    return Xbasis
    
    
def XYfunc(Xm, Zn, XYparams, coeffs):
    '''
    Given X and Z today generate X tomorrow
    '''
    # take natural logs of Xm 
    Xm = np.log(Xm)
    # concatenate Xm and Zn
    XZin = np.append(Xm, Zn)
    # choose from menu of functional forms
    if regtype == 'poly1':
        XYbasis = poly1(XZin, XYparams)
    XYout = np.dot(XYbasis, coeffs)
    Xn = XYout[0:nx]
    #Yn = XYout[nx:nx+ny]  
    # convert from logs to levels
    Xn = np.exp(Xn)
    return Xn
    
    
def MVOLS(Y, X):
    '''
    OLS regression with observations in rows
    '''
    XX = np.dot(np.transpose(X), X)
    XY = np.dot(np.transpose(X), Y)
    coeffs = np.dot(np.linalg.inv(XX), XY)
    return coeffs
    

# main program

# declare model parameters
# set parameter values
alpha = .35
beta = .99
gamma = 2.5
delta = .08
chi = 10.
theta = 2.
tau = .05   # the 1st stochastic shock
rho = .9
sigma = .01
s = 0.1

# make parameter list to pass to functions
mparams = np.array([alpha, beta, gamma, delta, chi, theta, tau, rho, sigma])
nx = 1
ny = 0
nz = 1

NN = rho  # VAR matrix for stochastic shocks
Sig = sigma # VCV matrix
Sigsr = np.sqrt(Sig) # square root of VCV matrix


# declare other parameters
T = 20   # number of observations to simulate
regtype = 'poly1' # functional form for X & Y functions 
fittype = 'MVOLS'   # regression fitting method
pord = 3  # order of polynomial for fitting function
ccrit = 1.0E-8  # convergence criteria for coeffs change
damp = 0.05   # damping paramter for fixed point algorithm
maxit = 500  # maximum number of iterations for fixed point algorithm
XYparams = (regtype, fittype, pord, nx, ny, nz, ccrit, damp)

#############################################################
# find model steady state

# take a guess for steady state values of k and ell
guessX = np.array([.1])

# find the steady state values using LinApp_FindSS
Zbar = np.zeros(nz)
Xbar = LinApp_FindSS(Modeldyn, mparams, guessX, Zbar, nx, ny)
kbar = Xbar

# set up steady state input vector
theta0 = np.array([kbar, kbar, kbar, 0., 0.])

# check SS solution
check = Modeldyn(theta0, mparams)
print ('check SS: ', check)
if np.max(np.abs(check)) > 1.E-6:
    print ('Have NOT found steady state')
    
Xbar = XYbar[0:nx]
#Ybar = XYbar[nx:nx+ny]
print('Xbar: ', Xbar)
#print('Ybar: ', Ybar)

# create history of Z's
Z = np.zeros([T,nz])
for t in range(1,T):
    Z[t,:] = rho*Z[t-1] + np.random.randn(1)*sigma
# declare initial guess for coefficients
if regtype == 'poly1':
    cnumb = int(pord*(nx+nz) + .5*(nx+nz-1)*(nx+nz-2))
    coeffs = np.ones((cnumb,(nx+ny)))*.1
    for i in range(0, nx+ny) :
        coeffs[:,i] = coeffs[:,i]*(i+1.)
    
# declare starting values
Xstart = np.ones(nx)*2

# begin fixed point iteration
dist = 1.
count = 0
while dist > ccrit:
    # check for maximum number of iterations
    count = count + 1
    if count > maxit:
        break
    # initialize X and Y series
    X = np.zeros((T,nx))
    
    # constuct X and Y series
    X[0] = XYfunc(Xstart, Z[0], XYparams, coeffs)
    for t in range(1,T):
        X[t] = XYfunc(X[t-1], Z[t-1], XYparams, coeffs)
    
    # plot time series
    timeperiods = np.asarray(range(0,T))
    plt.plot(timeperiods, X, label='X')
    plt.plot(timeperiods, Y, label='Y')
    plt.title('time series')
    plt.xlabel('time')
    plt.legend(loc=9, ncol=(nx+ny))
    plt.show()    
    
    # initialize Gam and Lam series
    Gam = np.zeros((T,nx))
    Lam = np.zeros((T,ny))
    
    # generate discrete support for epsilon to be used in expectations
    # using rectangular arbitrage
    # Eps are the central values
    # Phi are the associated probabilities
    npts = 2
    Eps = np.zeros(npts);
    Cum = np.linspace(0.0, 1.0, num=npts+1)+.5/npts
    Cum = Cum[0:npts]
    Phi = np.ones(npts)/npts
    Eps = norm.ppf(Cum)
    
    # construct Gam and Lam series
    for i in range(0, npts):
        for j in range(0,npts):
            theta01 = np.concatenate((X[1], X[0], Xstart, Y[1], Y[0], Z[1], Z[0]),axis=0)
            tGam, tLam = Modeldyn1(theta01, mparams)
            Gam[0] = Gam[0] + tGam*Phi[i]*Phi[j]
            Lam[0] = Lam[0] + tLam*Phi[i]*Phi[j]
    for t in range(1,T):
        for i in range(0,npts):
            for j in range(0,npts):
                Xp, Yp = XYfunc(X[t], Z[t], XYparams, coeffs)
                theta02 = np.concatenate((Xp, X[t], X[t-1], Yp, Y[t], Z[t], Z[t-1]),axis=0)
                tGam, tLam = Modeldyn1(theta02, mparams)
                Gam[t] = Gam[t] + tGam*Phi[i]*Phi[j]
                Lam[t] = Lam[t] + tLam*Phi[i]*Phi[j]
    
    # update values for X and Y
    #Gam = np.abs(Gam)
    #Lam = np.abs(Lam)
    Xnew = (Gam)*X
    Ynew = (Lam)*Y
    
    # run nonlinear regression to get new coefficients
    XZ = np.append(Xnew, Z, axis = 1)
    XY = np.append(Xnew, Ynew, axis = 1)
    XZ = XZ[0:T-1]
    XY = XY[1:T]
    if regtype == 'poly1':
        XZbasis = poly1(XZ[0], XYparams)
        XZbasis = np.atleast_2d(XZbasis)
        for t in range(1, T-1):
            temp = poly1(XZ[t], XYparams)
            temp = np.atleast_2d(temp)
            XZbasis = np.append(XZbasis, temp, axis=0)       
    if fittype == 'MVOLS':
        coeffsnew = MVOLS(XY, XZbasis)
        
    # calculate distance between coeffs and coeffsnew
    diff = coeffs - coeffsnew
    print('coeffs', coeffs)
    print('coeffsnew', coeffsnew)
    print('X', X)
    print('Y', Y)

    dist = np.max(np.abs(diff))  
    
    print('count ', count, 'distance', dist)
    
    # update coeffs
    coeffs = (1-damp)*coeffs + damp*coeffsnew