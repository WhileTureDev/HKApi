# utils/circuit_breaker.py

import pybreaker
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create a circuit breaker for database operations
db_circuit_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    state_storage=pybreaker.CircuitMemoryStorage(state=pybreaker.STATE_CLOSED),
)

@db_circuit_breaker
def call_database_operation(db_function, *args, **kwargs):
    try:
        return db_function(*args, **kwargs)
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        raise
