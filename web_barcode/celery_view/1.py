import time
from multiprocessing import Process


def very_long_func():

    time.sleep(60)


def test_func():
    print('Я еще не прошел time')
    # very_long_func()
    p1 = Process(target=very_long_func, daemon=True)
    p1.start()
    p1.join()
    print('Я все прошел')


test_func()
