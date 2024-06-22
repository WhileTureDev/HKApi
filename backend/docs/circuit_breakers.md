# Circuit Breakers

## Overview
Circuit breakers are an important pattern in microservice architecture that allows a system to handle failures gracefully. When a failure is detected, the circuit breaker trips, and subsequent calls fail immediately instead of waiting for a timeout. This prevents the system from becoming overwhelmed by failed requests.

## Implementation
In this project, we have implemented circuit breakers using the `pybreaker` library. This ensures that our system can degrade gracefully in the event of a failure.

## Usage
The circuit breaker is used in our database operations to handle potential database failures. Below is a sample implementation:

1. **Define the Circuit Breaker**

   ```python
   import pybreaker

   db_circuit_breaker = pybreaker.CircuitBreaker(
       fail_max=5,
       reset_timeout=60,
       state_storage=pybreaker.CircuitMemoryStorage(state=pybreaker.STATE_CLOSED)
   )
