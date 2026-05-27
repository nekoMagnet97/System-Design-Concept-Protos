# Python MySQL Connection Pool Prototype

A small prototype to understand the difference between:

1. Creating a new database connection for every thread/request
2. Reusing a fixed number of database connections through a bounded blocking connection pool

The goal of this project is not to build a production-ready pool, but to explore the core concurrency and systems concepts behind connection pooling.

---

# Motivation

Opening a new database connection is expensive.

Each connection may involve:
- TCP socket creation
- authentication
- session allocation
- server-side bookkeeping

If every thread creates its own connection, the system can quickly run into:
- high latency
- connection limits
- excessive resource usage
- poor scalability

Connection pools solve this by reusing a limited number of already-open connections.

---

# What This Prototype Demonstrates

## Non-pooled approach

Each thread:
1. Creates a new MySQL connection
2. Executes a query
3. Closes the connection

This maximizes connection creation overhead.

---

## Pooled approach

A fixed number of reusable connections are created ahead of time.

Threads:
1. Acquire a connection from a bounded blocking queue
2. Execute a query
3. Return the connection back to the pool

If all connections are in use:
- threads block and wait
- concurrency is naturally limited by pool size

This demonstrates:
- resource reuse
- bounded concurrency
- backpressure
- producer/consumer coordination

---

# Core Concept

A connection pool is not just a cache of connections.

It is also a concurrency control mechanism.

Even if 500 threads exist, a pool size of 5 means:
- only 5 database operations can happen concurrently

The queue enforces this limit safely.

---

# Technologies Used

- Python
- `mysql-connector-python`
- `threading`
- `queue.Queue`

---

# Running the Prototype

Install dependencies:

```bash
pip install mysql-connector-python
```

Update database credentials inside:

```python
getNewConnection()
```

Run:

```bash
python main.py
```

---

# Example Benchmark

```python
for poolSize, numThreads in [(5, 500), (10, 500), (20, 500), (50, 500)]:
    benchmarkPooled(poolSize, numThreads)
```

---

# Important Notes

This is intentionally a minimal educational prototype.

It does NOT include:
- connection health checks
- stale connection cleanup
- retry logic
- async support
- production-grade error handling

The purpose is to understand the underlying concurrency behavior, not to replace existing pooling libraries.

---

# Key Takeaways

- Opening database connections repeatedly is expensive
- Reusing connections improves throughput and reduces overhead
- A bounded queue naturally limits concurrency
- Thread count and database concurrency are not the same thing
- Connection pools are fundamentally resource management systems