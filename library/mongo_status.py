"""Simple runtime status holder for MongoDB connectivity.

Other modules import this to check whether the application successfully
connected to MongoDB during startup and to display a friendly message
when the DB is unavailable.
"""
connected = False
error = None


def set_status(is_connected: bool, err=None):
    global connected, error
    connected = bool(is_connected)
    error = None if err is None else str(err)


def get_status():
    return connected, error
