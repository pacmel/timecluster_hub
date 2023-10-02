# ----------------------------------------------------------------------
# Copyright (c) 2017, Jin-Man Park. All rights reserved.
# Contributors: Jin-Man Park and Jong-hwan Kim
# Affiliation: Robot Intelligence Technology Lab.(RITL), Korea Advanced Institute of Science and Technology (KAIST)
# URL: http://rit.kaist.ac.kr
# E-mail: jmpark@rit.kaist.ac.kr
# Citation: Jin-Man Park, and Jong-Hwan Kim. "Online recurrent extreme learning machine and its application to
# time-series prediction." Neural Networks (IJCNN), 2017 International Joint Conference on. IEEE, 2017.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
# ----------------------------------------------------------------------
# This code is originally from Numenta's Hierarchical Temporal Memory (HTM) code
# (Numenta Platform for Intelligent Computing (NuPIC))
# And modified to run Online Recurrent Extreme Learning Machine (OR-ELM)
# ----------------------------------------------------------------------

import numpy as np
from numpy.linalg import pinv
from numpy.linalg import inv
"""
Implementation of the fully online-sequential extreme learning machine (FOS-ELM)
Reference:
Wong, Pak Kin, et al. "Adaptive control using fully online sequential-extreme learning machine
and a case study on engine air-fuel ratio regulation." Mathematical Problems in Engineering 2014 (2014).
Note that the only difference between FOS-ELM and OS-ELM is in the initialize phase.
"""

def orthogonalization(Arr):
  [Q, S, _] = np.linalg.svd(Arr)
  tol = max(Arr.shape) * np.spacing(max(S))
  r = np.sum(S > tol)
  Q = Q[:, :r]

  return Q

def linear(features, weights, bias):
  
  assert(features.shape[1] == weights.shape[1]), \
    "features shape ("+str(features.shape[1]) +") must be equal to weights shape (" + str(weights.shape[1]) +")"
  (numSamples, numInputs) = features.shape
  (numHiddenNeuron, numInputs) = weights.shape
  V = np.dot(features, np.transpose(weights)) + bias
  
  #for i in range(numHiddenNeuron):
  #  V[:, i] += bias[0, i]

  return V

def sigmoidActFunc(V):
  H = 1 / (1+np.exp(-V))
  return H



class FOSELM(object):
  def __init__(self, inputs, outputs, numHiddenNeurons, activationFunction, LN=False, forgettingFactor=0.999, ORTH = False,RLS=False):

    self.activationFunction = activationFunction
    self.inputs = inputs
    self.outputs = outputs
    self.numHiddenNeurons = numHiddenNeurons

    # input to hidden weights
    self.inputWeights = np.random.random((self.numHiddenNeurons, self.inputs))
    self.ORTH = ORTH

    # bias of hidden units
    self.bias = np.random.random((1, self.numHiddenNeurons)) * 2 - 1
    # hidden to output layer connection
    self.beta = np.random.random((self.numHiddenNeurons, self.outputs))
    self.LN = LN
    # auxiliary matrix used for sequential learning
    self.M = None
    self.forgettingFactor = forgettingFactor
    self.RLS=RLS

  def layerNormalization(self, H, scaleFactor=1, biasFactor=0):

    H_normalized = (H - H.mean()) / (np.sqrt(H.var() + 0.0001))
    H_normalized = scaleFactor * H_normalized + biasFactor

    return H_normalized

  def calculateHiddenLayerActivation(self, features):
    """
    Calculate activation level of the hidden layer
    :param features feature matrix with dimension (numSamples, numInputs)
    :return: activation level (numSamples, numHiddenNeurons)
    """
    if self.activationFunction == "sig":
      V = linear(features, self.inputWeights,self.bias)
      if self.LN:
        V = self.layerNormalization(V)
      H = sigmoidActFunc(V)
      print("V ~ ", V.shape)
      print("H ~ ", H.shape)
    else:
      print ("FOS-ELM l-95 Unknown activation function type: " + self.activationFunction)
      raise NotImplementedError

    return H


  def initializePhase(self, lamb=0.0001):
    """
    Step 1: Initialization phase
    """
    # randomly initialize the input->hidden connections
    self.inputWeights = np.random.random((self.numHiddenNeurons, self.inputs))
    self.inputWeights = self.inputWeights * 2 - 1

    if self.ORTH:
      if self.numHiddenNeurons > self.inputs:
        self.inputWeights = orthogonalization(self.inputWeights)
      else:
        self.inputWeights = orthogonalization(self.inputWeights.transpose())
        self.inputWeights = self.inputWeights.transpose()

    if self.activationFunction == "sig":
      self.bias = np.random.random((1, self.numHiddenNeurons)) * 2 - 1
    else:
      print ("119: Unknown activation function type: " + self.activationFunction)
      raise NotImplementedError

    self.M = inv(lamb*np.eye(self.numHiddenNeurons))
    self.beta = np.zeros([self.numHiddenNeurons,self.outputs])



  def train(self, features, targets):
    """
    Step 2: Sequential learning phase
    :param features feature matrix with dimension (numSamples, numInputs)
    :param targets target matrix with dimension (numSamples, numOutputs)
    """
    (numSamples, numOutputs) = targets.shape
    assert features.shape[0] == targets.shape[0], \
      "FOS_ELM:train: differs features "+str(features.shape[0])+" targets "+str(targets.shape[0])

    H = self.calculateHiddenLayerActivation(features)
    Ht = np.transpose(H)

    if self.RLS:

      self.RLS_k = np.dot(np.dot(self.M,Ht),inv( 
        self.forgettingFactor*np.eye(numSamples)+ np.dot(H,np.dot(self.M,Ht))))
      self.RLS_e = targets - np.dot(H,self.beta)
      self.beta = self.beta + np.dot(self.RLS_k,self.RLS_e)
      self.M = 1/(self.forgettingFactor)*(self.M - np.dot(self.RLS_k,np.dot(H,self.M)))

    else:
      print("non RLS")
      print("targets ~ " + str(targets.shape))
      print("H ~ " + str(H.shape))
      print("Ht ~ " + str(Ht.shape))
      I = np.eye(numSamples)
      factor = (1/self.forgettingFactor)
      factor_M = factor * self.M
      print("Get temp1")
      temp1 = np.dot(H, factor_M)
      print("Get temp2")
      temp2 = np.dot(factor_M, Ht)
      print("I ~ " + str(I.shape) + "H ~ " + str(H.shape) + "temp2 ~ " + str(temp2.shape))
      covariance_matrix = I+np.dot(H, temp2)
      print("covariance matrix ~ " + str(covariance_matrix.shape))
      inverse_covariance_matrix = pinv(covariance_matrix)
      print("inverse" + str(inverse_covariance_matrix.shape)  + "temp1 ~ " + str(temp1.shape))
      self.M = factor_M - np.dot(
        factor_M, np.dot(Ht, np.dot(inverse_covariance_matrix, temp1))
      )
      
      print("self.M ~ ", self.M.shape)
      print("H ~ ", H.shape)
      print("Beta ~ ", self.beta.shape)
      print("Targets ~ ", targets.shape)
      product = np.dot(H, self.beta)
      print("Product ~", product.shape )
      diff = targets - product
      product = np.dot(self.M, np.dot(Ht, diff))
      print("Product2 ~ ", product.shape)
      self.beta = self.beta + product
      
      #self.beta = self.beta + np.dot(self.M, np.dot(Ht, targets - 
      #                                              np.dot(H, self.beta)))
      # self.beta = (self.forgettingFactor)*self.beta + np.dot(self.M, np.dot(Ht, targets - np.dot(H, (self.forgettingFactor)*self.beta)))
      # self.beta = (self.forgettingFactor)*self.beta + (self.forgettingFactor)*np.dot(self.M, np.dot(Ht, targets - np.dot(H, self.beta)))

  def predict(self, features):
    """
    Make prediction with feature matrix
    :param features: feature matrix with dimension (numSamples, numInputs)
    :return: predictions with dimension (numSamples, numOutputs)
    """
    H = self.calculateHiddenLayerActivation(features)
    prediction = np.dot(H, self.beta)
    return prediction

