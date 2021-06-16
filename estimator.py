from abc import ABC, abstractmethod
import sys
import math
from sortedcontainers import SortedList

class Accumulator(ABC):
    @abstractmethod
    def accumulate(self, value) -> None:
        pass

    @abstractmethod
    def get_current(self) -> float:
        pass

class MeanAccumulator(Accumulator):
    def __init__(self) -> None:
        super().__init__()

        self.sum = 0
        self.prev_sum = 0
        self.count = 0
    
    def accumulate(self, value) -> None:
        self.prev_sum = self.sum
        self.sum += value
        self.count += 1
    
    def get_current(self) -> float:
        return self.sum / self.count
    
    def get_previous(self) -> float:
        return self.prev_sum / max(self.count - 1, 1)

class StdDevAccumulator(Accumulator):
    def __init__(self, meanAccumulator) -> None:
        super().__init__()
        self.meanAcc = meanAccumulator
        self.m2n = 0.0  
    
    # must be called after meanaccumulator. I need to fix this eventually
    def accumulate(self, value) -> None:
        self.m2n = self.m2n + (value - self.meanAcc.get_previous()) * (value - self.meanAcc.get_current())

    def get_current(self) -> float:
        return math.sqrt(self.m2n / self.meanAcc.count)

class MedianAccumulator(Accumulator):
    def __init__(self) -> None:
        super().__init__()
        # utilizing an outside library for optimization, as I did not want to re-implement the wheel for this problem
        self.sorted_list = SortedList([])
    
    def accumulate(self, value) -> None:
        self.sorted_list.add(value)
    
    def get_current(self) -> float:
        median = 0.0
        index = len(self.sorted_list) // 2
        if len(self.sorted_list) % 2 == 0:
            median = (self.sorted_list[index] + self.sorted_list[index - 1]) / 2
        else:
            median = self.sorted_list[index]
        return median

class Estimator(ABC):
    @abstractmethod
    def add_next(self, val) -> None:
        pass

    @abstractmethod
    def get_mean(self) -> float:
        pass

    @abstractmethod
    def get_stddev(self) -> float:
        pass

    @abstractmethod
    def get_median(self) -> float:
        pass

class MainEstimator(Estimator):
    def __init__(self) -> None:
        super().__init__()
        self.meanAcc = MeanAccumulator()
        self.stddevAcc = StdDevAccumulator(self.meanAcc)
        self.medianAcc = MedianAccumulator()
    
    def add_next(self, val) -> None:
        self.meanAcc.accumulate(val) # Important! Must go before stddev accumulator. Need to fix dependency
        self.stddevAcc.accumulate(val)
        self.medianAcc.accumulate(val)
    
    def get_mean(self) -> float:
        return self.meanAcc.get_current()
    
    def get_median(self) -> float:
        return self.medianAcc.get_current()
    
    def get_stddev(self) -> float:
        return self.stddevAcc.get_current()


estimator = MainEstimator()
print('please input newline separated floating point numbers')
while True:
    next_val = sys.stdin.readline()
    if next_val.lower() == 'exit\n':
        print('program exiting')
        sys.exit(0)
    
    try:
        next_val = float(next_val)
    except:
        print('please ensure all values are valid floating point numbers')
        sys.exit(1)
    
    estimator.add_next(next_val)
    print(f'{estimator.get_mean():.3f}, {estimator.get_stddev():.3f}, {estimator.get_median():.3f}')
