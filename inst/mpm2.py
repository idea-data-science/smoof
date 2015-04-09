import copy
import math
import random

import numpy as np

class MultiplePeaksModel2:
    """A test problem
    """

    class Peak(list):
        """Helper class that maintains the data structures needed for one peak."""

        def __init__(self, numberVariables, height, shape, radius, position=None, minLimits=None, maxLimits=None, rotated=True):
            # shortcuts and initialization
            cos = math.cos
            sin = math.sin
            runi = random.uniform
            if position is None:
                position = np.random.rand(numberVariables).tolist()
            if minLimits is None:
                minLimits = [0.0] * numberVariables
            if maxLimits is None:
                maxLimits = [1.0] * numberVariables
            # generate random rotation matrix
            rotationMatrix = np.eye(numberVariables)
            if rotated:
                quarterPi = math.pi / 4.0
                for j in xrange(numberVariables - 1):
                    for k in xrange(j + 1, numberVariables):
                        r = np.eye(numberVariables)
                        alpha = runi(-quarterPi, quarterPi)
                        r[j,j] = cos(alpha)
                        r[j,k] = sin(alpha)
                        r[k,j] = -sin(alpha)
                        r[k,k] = cos(alpha)
                        rotationMatrix = np.dot(rotationMatrix, r)
            # generate inverse 'covariance' matrix from rotation matrix
            varianceRange = (np.array(maxLimits) - np.array(minLimits)) / 20.0
            scaledDiagValues = np.random.rand(numberVariables) * varianceRange + varianceRange * 0.05
            self.D = np.dot(np.dot(rotationMatrix.T, np.diag(scaledDiagValues)), rotationMatrix)
            self.D = np.linalg.inv(self.D)
            # other data
            list.__init__(self, position)
            self.height = height
            self.shape = shape
            self.radius = radius


    def __init__(self, numberVariables=10, peaks=None):
        #TestProblem.__init__(self, [ObjectiveFunction(self.objectiveFunction, False)], minObjectiveLimits=[0.0], maxObjectiveLimits=[1.0])
        self.numberVariables = numberVariables
        self.minLimits = [0.0] * numberVariables
        self.maxLimits = [1.0] * numberVariables
        self.peaks = peaks
        if peaks is None:
            self.peaks = self.randomUniformPeaks(numberVariables)
        self.isDeterministic = True


    @classmethod
    def createInstanceWithExactNumberOfOptima(cls, numberOptima, numberVariables, topology, shapeHeightCorrelation, rotatedPeaks=True):
        shapeRange = (1.5, 2.5)
        radiusRange = (0.25 * math.sqrt(numberVariables), 0.5 * math.sqrt(numberVariables))
        heightRange = (0.5, 0.99)
        globalOptimum = cls.randomUniformPeaks(1, numberVariables, numberGlobalOptima=1, heightRange=heightRange, shapeRange=shapeRange, radiusRange=radiusRange, rotated=rotatedPeaks)[0]
        if topology == "random":
            peaks = cls.randomUniformPeaks(numberOptima - 1, numberVariables, numberGlobalOptima=0, heightRange=heightRange, shapeRange=shapeRange, radiusRange=radiusRange, rotated=rotatedPeaks)
        elif topology == "funnel":
            peaks = cls.clusteredPeaks(numberOptima - 1, numberVariables, numberGlobalOptima=0, heightRange=heightRange, shapeRange=shapeRange, radiusRange=radiusRange, rotated=rotatedPeaks, clusterCenter=globalOptimum)
        peaks.append(globalOptimum)
        problem = cls.createInstance(peaks, topology, shapeHeightCorrelation)
        currentNumberOptima = len(problem.getLocalOptima())
        factor = 1.0
        while currentNumberOptima < numberOptima * 0.8 and factor > 0.01:
            peaksCopy = copy.deepcopy(peaks)
            for peak in peaksCopy:
                peak.radius *= 0.95
            problem = cls.createInstance(peaks, topology, shapeHeightCorrelation)
            currentNumberOptima = len(problem.getLocalOptima())
            if currentNumberOptima < numberOptima:
                peaks = peaksCopy
            factor *= 0.95
        radiusRange = (radiusRange[0] * factor, radiusRange[1] * factor)
        problem = cls.createInstance(peaks, topology, shapeHeightCorrelation)
        currentNumberOptima = len(problem.getLocalOptima())
        previousNumberOptima = currentNumberOptima
        while currentNumberOptima < numberOptima:
            tries = 0
            height = random.uniform(*heightRange)
            while currentNumberOptima != previousNumberOptima + 1:
                # generate list of 1 random new peak
                if topology == "random":
                    newPeaks = cls.randomUniformPeaks(1, numberVariables, numberGlobalOptima=0, heightRange=heightRange, shapeRange=shapeRange, radiusRange=radiusRange, rotated=rotatedPeaks)
                elif topology == "funnel":
                    newPeaks = cls.clusteredPeaks(1, numberVariables, numberGlobalOptima=0, heightRange=heightRange, shapeRange=shapeRange, radiusRange=radiusRange, rotated=rotatedPeaks, clusterCenter=globalOptimum)
                problem = cls.createInstance(peaks + newPeaks, topology, shapeHeightCorrelation)
                currentNumberOptima = len(problem.getLocalOptima())
                tries += 1
            previousNumberOptima = currentNumberOptima
            peaks.extend(newPeaks)
        return problem


    @classmethod
    def createInstance(cls, peaks, topology="random", shapeHeightCorrelation=0):
        assert(shapeHeightCorrelation in (-1, 0, 1))
        # attention: deepcopy is important because peak objects are
        # modified in the following
        peaksCopy = copy.deepcopy(peaks)
        numberVariables = len(peaksCopy[0])
        for peak in peaksCopy:
            assert(len(peak) == numberVariables)
        if topology == "funnel":
            # sort peaks according to height (descending)
            peaksDecorated = [(peak.height, peak) for peak in peaksCopy]
            peaksDecorated.sort(reverse=True)
            heights = [height for height, _ in peaksDecorated]
            # set global optimum as center
            center = peaksDecorated[0][1]
            peaksDecorated = []
            for peak in peaksCopy:
                dist = sum((c - p) ** 2 for c, p in zip(center, peak))
                peaksDecorated.append((dist, peak))
            peaksDecorated.sort()
            peaksCopy = [peak for _, peak in peaksDecorated]
            # make heights anti-correlated to distance to center
            for height, peak in zip(heights, peaksCopy):
                peak.height = height
        elif topology == "random":
            # nothing to do, everything is random
            pass
        else:
            raise Exception("undefined topology")
        if shapeHeightCorrelation != 0:
            shapes = [peak.shape for peak in peaksCopy]
            antiCorrelated = (shapeHeightCorrelation == -1)
            shapes.sort(reverse=antiCorrelated)
            peaksDecorated = [(peak.height, peak) for peak in peaksCopy]
            peaksDecorated.sort()
            peaksCopy = [peak for _, peak in peaksDecorated]
            for peak, shape in zip(peaksCopy, shapes):
                peak.shape = shape
        problem = cls(numberVariables, peaksCopy)
        return problem


    @classmethod
    def clusteredPeaks(cls, numberPeaks=8, numberVariables=10, numberGlobalOptima=1, heightRange=(0.5, 0.99), shapeRange=(1.75, 2.25), radiusRange=(0.25, 0.5), rotated=True, clusterCenter=None):
        assert(numberPeaks >= numberGlobalOptima)
        runi = random.uniform
        if clusterCenter is None:
            # determine random uniform cluster center
            clusterCenter = np.random.rand(numberVariables)
        peaks = []
        for i in xrange(numberPeaks):
            position = np.random.randn(numberVariables) / 6.0 * math.sqrt(numberVariables) + clusterCenter
            # repair box constraint violations of position
            for j in xrange(numberVariables):
                while position[j] < 0.0 or 1.0 < position[j]:
                    if 1.0 < position[j]:
                        position[j] = 1.0 - (position[j] - 1.0)
                    elif position[j] < 0.0:
                        position[j] = -position[j]
            # build peak
            peaks.append(cls.Peak(numberVariables, runi(*heightRange), runi(*shapeRange), runi(*radiusRange), position=position.tolist(), rotated=rotated))
        globalOptima = random.sample(peaks, numberGlobalOptima)
        for opt in globalOptima:
            opt.height = 1.0
        return peaks


    @classmethod
    def randomUniformPeaks(cls, numberPeaks=8, numberVariables=10, numberGlobalOptima=1, heightRange=(0.5, 0.99), shapeRange=(1.75, 2.25), radiusRange=(0.25, 0.5), rotated=True):
        numberRemainingPeaks = numberPeaks - numberGlobalOptima
        assert(numberRemainingPeaks >= 0)
        runi = random.uniform
        peaks = [cls.Peak(numberVariables, 1.0, runi(*shapeRange), runi(*radiusRange), rotated=rotated) for _ in xrange(numberGlobalOptima)]
        peaks.extend([cls.Peak(numberVariables, runi(*heightRange), runi(*shapeRange), runi(*radiusRange), rotated=rotated) for _ in xrange(numberRemainingPeaks)])
        return peaks


    @staticmethod
    def dist(phenome, peak):
        """Mahalanobis distance"""
        differenceVector = np.array(peak)
        differenceVector -= phenome
        return math.sqrt(np.dot(np.dot(differenceVector, peak.D), differenceVector))


    def g(self, phenome, peak):
        distance = self.dist(phenome, peak)
        return peak.height / (1.0 + math.pow(distance, peak.shape) / peak.radius)


    def objectiveFunction(self, phenome):
        g = self.g
        phenome = np.array(phenome)
        maxGValue = max(g(phenome, peak) for peak in self.peaks)
        return 1.0 - maxGValue


    def getActivePeak(self, phenome):
        g = self.g
        maxObjectiveValue = -1.0
        activePeak = None
        for peak in self.peaks:
            objectiveValue = g(phenome, peak)
            if objectiveValue > maxObjectiveValue:
                activePeak = peak
                maxObjectiveValue = objectiveValue
        return activePeak


    def getBasin(self, phenome):
        getActivePeak = self.getActivePeak
        previousPeak = phenome
        currentPeak = getActivePeak(previousPeak)
        while previousPeak != currentPeak:
            previousPeak = currentPeak
            currentPeak = getActivePeak(currentPeak)
        return currentPeak


    def getLocalOptima(self):
        # shortcuts
        minLimits = self.minLimits
        maxLimits = self.maxLimits
        getActivePeak = self.getActivePeak
        # test peaks
        localOptima = []
        peaks = np.vstack(self.peaks)
        for i, peak in enumerate(peaks):
            if getActivePeak(peak) is self.peaks[i]:
                localOptima.append(list(peak))
        return localOptima


    def getOptimalSolutions(self):
        # shortcuts
        minLimits = self.minLimits
        maxLimits = self.maxLimits
        # test peaks
        opts = []
        maxHeight = -1.0
        genomes = []
        for peak in self.peaks:
            if peak.height > maxHeight:
                genomes = [list(peak)]
                maxHeight = peak.height
            elif peak.height == maxHeight:
                genomes.append(list(peak))
        for genome in genomes:
            opts.append(list(genome))
        return opts



#####################################################################################################
# stuff for the R interface:
#####################################################################################################


currentProblem = None
currentNpeaks = None
currentDimension = None
currentTopology = None
currentSeed = None



def initProblem(npeaks, dimension, topology, randomSeed):
    global currentProblem, currentNpeaks, currentDimension, currentTopology, currentSeed
    if (currentNpeaks != npeaks or currentDimension != dimension or currentTopology != topology or currentSeed != randomSeed):
      currentNpeaks = npeaks
      currentDimension = dimension
      currentTopology = topology
      currentSeed = randomSeed
      random.seed(randomSeed)
      np.random.seed(randomSeed)
      currentProblem = MultiplePeaksModel2.createInstanceWithExactNumberOfOptima(npeaks, dimension, topology, shapeHeightCorrelation = 0, rotatedPeaks = True)

def evaluateProblem(position, npeaks, dimension, topology, randomSeed):
    global currentProblem
    initProblem(npeaks, dimension, topology, randomSeed)
    return currentProblem.objectiveFunction(position)

if __name__ == "__main__":
    # nothing to do here
    pass
