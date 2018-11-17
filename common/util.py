import time

class Stopwatch(object):
    start_time = 0
    stop_time = 0
    
    @staticmethod
    def start():
        Stopwatch.start_time = time.time()
        
    @staticmethod
    def stop():
        Stopwatch.stop_time = time.time()
        
    @staticmethod
    def get_time_elapsed():
        return Stopwatch.stop_time - Stopwatch.start_time
    
    @staticmethod
    def get_formatted_time(timestamp:float=None):
        if timestamp:
            seconds_elapsed = timestamp
        else:
            seconds_elapsed = Stopwatch.get_time_elapsed()
        
        hours = int(seconds_elapsed / 3600)
        seconds_elapsed -= hours*3600
        
        minutes = int(seconds_elapsed / 60)
        seconds_elapsed -= minutes*60
        
        seconds = seconds_elapsed
        
        return '{0}:{1}:{2:09.6f}'.format(str(hours).zfill(2),
                                          str(minutes).zfill(2),
                                          seconds)