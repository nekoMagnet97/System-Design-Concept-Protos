import mysql.connector
import queue
import threading
import time


def getNewConnection():
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="",
        database="prototype",
    )


class ConnectionPool:
    def __init__(self, pool_size=5):
        self.pool_size = pool_size
        self._queue = queue.Queue(maxsize=pool_size)
        for _ in range(pool_size):
            self._queue.put(getNewConnection())

    def getConnection(self):
        return self._queue.get()

    def releaseConnection(self, connection):
        self._queue.put(connection)

    def close(self):
        while True:
            try:
                self._queue.get_nowait().close()
            except queue.Empty:
                break


def runWorkload(connection):
    with connection.cursor() as cursor:
        cursor.execute("SELECT SLEEP(0.01)")
        cursor.fetchone()


def worker(acquire, release, failed_count, failed_lock):
    connection = None
    failed = False
    try:
        connection = acquire()
        runWorkload(connection)
    except Exception:
        failed = True
    finally:
        if connection is not None:
            try:
                release(connection)
            except Exception:
                failed = True
    if failed:
        with failed_lock:
            failed_count[0] += 1


def benchmark(num_threads, acquire, release, on_complete=None):
    failed_count = [0]
    failed_lock = threading.Lock()
    start_time = time.time()

    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(
            target=worker,
            args=(acquire, release, failed_count, failed_lock),
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    if on_complete is not None:
        on_complete()

    elapsed_time = time.time() - start_time
    print(f"Elapsed time: {elapsed_time:.3f} seconds")
    print(f"Workers failed: {failed_count[0]} / {num_threads}")


def benchmarkNonPooled(num_threads=250):
    benchmark(
        num_threads,
        acquire=getNewConnection,
        release=lambda conn: conn.close(),
    )


def benchmarkPooled(pool_size=5, num_threads=250):
    pool = ConnectionPool(pool_size)
    benchmark(
        num_threads,
        acquire=pool.getConnection,
        release=pool.releaseConnection,
        on_complete=pool.close,
    )

for num_threads in [50, 100, 200, 350, 500]:
    print(f"Pool size: NA, Number of threads: {num_threads}")
    benchmarkNonPooled(num_threads)
    print("--------------------------------")

for pool_size, num_threads in [(5, 500), (10, 500), (20, 500), (30, 1000)]:
    print(f"Pool size: {pool_size}, Number of threads: {num_threads}")
    benchmarkPooled(pool_size, num_threads)
    print("--------------------------------")
