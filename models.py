# models.py - the basic classes for the airport system


class AirportError(Exception):
    """Raised when someone tries to do something the airport rules don't allow."""


STATUSES = ["Scheduled", "Boarding", "Delayed", "Cancelled", "Departed"]

# Which status is allowed to come after which (this is our state machine diagram)
ALLOWED_CHANGES = {
    "Scheduled": ["Boarding", "Delayed", "Cancelled"],
    "Delayed": ["Scheduled", "Boarding", "Cancelled"],
    "Boarding": ["Delayed", "Departed", "Cancelled"],
    "Departed": [],
    "Cancelled": [],
}


class Flight:
    def __init__(self, number, origin, destination, departure, capacity):
        self.number = number
        self.origin = origin
        self.destination = destination
        self.departure = departure  # a datetime
        self.capacity = capacity
        self.status = "Scheduled"
        self.gate = None  # becomes a Gate object once one is assigned

    def is_open(self):
        # cancelled and departed flights can't be booked, checked in or boarded
        return self.status not in ("Cancelled", "Departed")

    def change_status(self, new_status):
        if new_status not in ALLOWED_CHANGES[self.status]:
            raise AirportError(f"{self.number} can't go from {self.status} to {new_status}")
        old_status = self.status
        self.status = new_status
        return old_status


class Gate:
    def __init__(self, code):
        self.code = code
        self.flight = None  # number of the flight using this gate right now

    def release(self):
        self.flight = None


class Passenger:
    def __init__(self, passenger_id, name, email):
        self.id = passenger_id
        self.name = name
        self.email = email


class Booking:
    def __init__(self, reference, passenger, flight):
        self.reference = reference
        self.passenger = passenger
        self.flight = flight
        self.seat = None
        self.checked_in = False
        self.boarded = False

    def state(self):
        if self.boarded:
            return "Boarded"
        if self.checked_in:
            return "Checked in"
        return "Booked"
