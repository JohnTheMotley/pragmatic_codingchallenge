from abc import ABC, abstractmethod
import sys
import math
from sortedcontainers import SortedList
from collections import defaultdict

class Storage(ABC):
    @abstractmethod
    def __len__(self):
        pass

    @abstractmethod
    def __getitem__(self, key) -> float:
        pass

    @abstractmethod
    def add(self, val) -> None:
        pass

class BasicStorage(Storage):
    def __init__(self) -> None:
        super().__init__()
        self.sortedList = SortedList()

    def __len__(self):
        return len(self.sortedList)
    
    def __getitem__(self, key) -> float:
        return self.sortedList[key]
    
    def add(self, val) -> None:
        self.sortedList.add(val)

class Accumulator(ABC):
    @abstractmethod
    def accumulate(self, val) -> None:
        pass

    @abstractmethod
    def get_current(self) -> float:
        pass

    def get_previous(self) -> float:
        pass

class OnlineMeanAccumulator(Accumulator):
    def __init__(self):
        self.sum = 0
        self.prev_sum = 0
        self.total = 0
    
    def accumulate(self, val) -> None:
        self.prev_sum = self.sum
        self.sum += val
        self.total += 1
    
    def get_current(self) -> float:
        return self.sum / max(1, self.total)
    
    def get_previous(self) -> float:
        return self.prev_sum / max(1, self.total - 1)

class OnlineStddevAccumulator(Accumulator):
    def __init__(self, meanAcc: Accumulator):
        self.meanAcc = meanAcc
        self.m2n = 0
        self.prev_m2n = 0
        self.count = 0
    
    # run after mean accumulator has accumulated
    def accumulate(self, val) -> None:
        self.count += 1
        self.prev_m2n = self.m2n
        self.m2n = self.m2n + (val - self.meanAcc.get_previous()) * (val - self.meanAcc.get_current())
    
    def get_current(self) -> float:
        return math.sqrt(self.m2n / max(1, self.count))
    
    def get_previous(self) -> float:
        return math.sqrt(self.m2n / max(1, self.count - 1))

class MedianAccumulator(Accumulator):
    def __init__(self, storage: Storage):
        self.storage = storage
        self.prev = 0
    
    def accumulate(self, val) -> None:
        # inefficient, as get_current() ends up called twice per object.
        # however, for good class design this class should not know exactly how its being called
        if len(self.storage) > 0:
            self.prev = self.get_current()
        self.storage.add(val)

    def get_current(self) -> float:
        index = len(self.storage) // 2
        median = 0.0
        if len(self.storage) % 2 == 0:
            median = (self.storage[index] + self.storage[index - 1]) / 2
        else:
            median = self.storage[index]
        return median

# tracks the median in a very limited viewing window, but uses limited memory
class FaultyMedianAccumulator(Accumulator):
    def __init__(self, windowSize = 1000) -> None:
        super().__init__()
        self.prev = 0
        self.median = 0
        self.windowSize = windowSize
        self.windowLeft = SortedList()
        self.windowRight = SortedList()     
    
    def accumulate(self, val) -> None:
        self.prev = self.median
        if val <= self.median:
            self.windowLeft.add(val)
            self.windowRight.add(self.median)
            self.median = self.windowLeft.pop(-1)
        else:
            self.windowRight.add(val)
            self.windowLeft.add(self.median)
            self.median = self.windowRight.pop(0)
        if len(self.windowLeft) > self.windowSize:
            leftIndex = len(self.windowLeft) // 2
            rightIndex = len(self.windowLeft)
            self.windowLeft = SortedList([val for val in self.windowLeft.islice(leftIndex, rightIndex)])
        if len(self.windowRight) > self.windowSize:
            leftIndex = 0
            rightIndex = len(self.windowRight) // 2
            self.windowRight = SortedList([val for val in self.windowRight.islice(leftIndex, rightIndex)])
    
    def get_current(self) -> float:
        return self.median

    def get_previous(self) -> float:
        return self.prev

class Estimator:
    def __init__(self, meanAcc: Accumulator, stddevAcc: Accumulator, medianAcc: Accumulator):
        self.meanAcc = meanAcc
        self.stddevAcc = stddevAcc
        self.medianAcc = medianAcc

    def accumulate(self, val) -> None:
        self.meanAcc.accumulate(val)
        self.stddevAcc.accumulate(val)
        self.medianAcc.accumulate(val)

    def get_mean(self) -> float:
        return self.meanAcc.get_current()

    def get_stddev(self) -> float:
        return self.stddevAcc.get_current()

    def get_median(self) -> float:
        return self.medianAcc.get_current()

# configuration
print('the following configuration commands can be skipped to assume default values')

# storage options, currently only the one available
storageMap = defaultdict(lambda: BasicStorage())

storage = storageMap['default']

# mean accumulators, currently only the one available
meanAccMap = defaultdict(lambda: OnlineMeanAccumulator())

meanAcc = meanAccMap['default']

# stddev accumulators, currently only the one available

stddevAccMap = defaultdict(lambda: OnlineStddevAccumulator(meanAcc))

stddevAcc = stddevAccMap['default']

# median accumulators, currently only one available
medianAccMap = defaultdict(lambda: MedianAccumulator(storage))
medianAccMap['faulty'] = FaultyMedianAccumulator()

print('the following median accumulator options are available')
print('\t"default" -- default median accumulator. O(n) storage, approximately O(log(n)) insertion')
print('\t"faulty" -- uses O(1) storage, but can quickly lose accuracy.')

option = sys.stdin.readline().strip()
medianAcc = medianAccMap[option]


estimator = Estimator(meanAcc, stddevAcc, medianAcc)
print('input floating point values, newline separated, to the estimator. input "exit" to quit.')
while True:
    next_val = sys.stdin.readline()
    if next_val.strip().lower() == 'exit':
        print('program exiting')
        sys.exit(0)
    
    try:
        next_val = float(next_val)
    except:
        print('please ensure all values are valid floating point numbers')
        continue
    
    estimator.accumulate(next_val)
    print(f'{estimator.get_mean():.3f}, {estimator.get_stddev():.3f}, {estimator.get_median():.3f}')
