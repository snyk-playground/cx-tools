````
This folder abstracts REST and V1 apis calls that have been used by some of the scripts
within cx-tools.

By design, the functions herein are wrapper functions that call an api and return the 
response payload back to the calling code, where the business logic to process that 
response is encapsulated. 

See integrations/utils/utils_func.py for an example of their use.