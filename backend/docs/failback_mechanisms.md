# Fallback Mechanisms

## Overview
Fallback mechanisms ensure that your application can still provide a minimum level of functionality even when some components fail. This improves the resilience and user experience by handling failures gracefully.

## Implementation
Fallback mechanisms can be implemented in various parts of the application. In this project, we use fallbacks for database operations and API calls. When a failure occurs, a default response is returned instead of an error.

## Usage

### Example for Audit Logs
1. **Define the Fallback Function**

   ```python
   # utils/fallbacks.py
   import logging

   logger = logging.getLogger(__name__)

   def get_default_audit_logs():
       logger.warning("Returning default audit logs due to failure")
       return [
           {
               "id": 0,
               "user_id": 0,
               "user_name": "unknown",
               "action": "default_action",
               "timestamp": "N/A",
               "details": "This is a fallback log entry."
           }
       ]
