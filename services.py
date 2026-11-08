# services.py - the actual airport logic

from datetime import datetime, timedelta

from models import AirportError, Flight, Gate, Passenger, Booking, STATUSES


# ---- Singleton pattern: one shared settings object for the whole airport ----

class AirportSettings:
    """Every service reads its settings from here, so there must only ever be one copy.
    AirportSettings() always gives back the same object."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.reset()
        return cls._instance

    def reset(self):
        self.checkin_closes_minutes = 60   # check-in closes this long before departure
        self.seat_letters = "ABCDEF"       # seats in each row


class FlightService:
    """Looks after flights and gates."""

    def __init__(self):
        self.flights = {}
        self.gates = {}
        self.listeners = []  # functions that want to hear about status changes (Observer)

    # ---- flights ----

    def add_flight(self, number, origin, destination, departure, capacity):
        number = number.upper()
        if number in self.flights:
            raise AirportError(f"Flight {number} already exists")
        if capacity < 1:
            raise AirportError("A flight needs at least 1 seat")
        flight = Flight(number, origin.upper(), destination.upper(), departure, capacity)
        self.flights[number] = flight
        return flight

    def get_flight(self, number):
        flight = self.flights.get(number.upper())
        if flight is None:
            raise AirportError(f"There is no flight {number.upper()}")
        return flight

    def list_flights(self):
        return sorted(self.flights.values(), key=lambda f: f.departure)

    def change_status(self, number, new_status):
        flight = self.get_flight(number)
        new_status = new_status.capitalize()
        if new_status not in STATUSES:
            raise AirportError(f"Unknown status '{new_status}'. Use one of: {', '.join(STATUSES)}")

        old_status = flight.change_status(new_status)

        # a flight that is cancelled or gone doesn't need its gate any more
        if not flight.is_open() and flight.gate:
            flight.gate.release()
            flight.gate = None

        self.tell_listeners(flight, old_status)
        return flight

    # ---- gates ----

    def add_gate(self, code):
        code = code.upper()
        if code in self.gates:
            raise AirportError(f"Gate {code} already exists")
        self.gates[code] = Gate(code)
        return self.gates[code]

    def assign_gate(self, number, code):
        flight = self.get_flight(number)
        gate = self.gates.get(code.upper())
        if gate is None:
            raise AirportError(f"There is no gate {code.upper()}")
        if not flight.is_open():
            raise AirportError(f"{flight.number} is {flight.status}, it doesn't need a gate")
        if gate.flight not in (None, flight.number):
            raise AirportError(f"Gate {gate.code} is already used by {gate.flight}")

        # if the flight was at another gate, free that one up
        if flight.gate and flight.gate is not gate:
            flight.gate.release()
        gate.flight = flight.number
        flight.gate = gate

    # ---- Observer pattern ----

    def add_listener(self, listener):
        self.listeners.append(listener)

    def tell_listeners(self, flight, old_status):
        for listener in self.listeners:
            try:
                listener(flight, old_status)
            except Exception as error:
                # a broken listener should never stop a status change
                print(f"(a listener failed: {error})")


# ---- Strategy pattern: each boarding rule is its own small class ----
# A rule raises AirportError if the passenger can't board, otherwise it does nothing.

class MustBeCheckedIn:
    def check(self, booking, flight):
        if not booking.checked_in:
            raise AirportError(f"{booking.passenger.name} has not checked in yet")


class BoardingMustBeOpen:
    def check(self, booking, flight):
        if flight.status != "Boarding":
            raise AirportError(f"Boarding is not open, {flight.number} is {flight.status}")


class NotAlreadyBoarded:
    def check(self, booking, flight):
        if booking.boarded:
            raise AirportError(f"{booking.passenger.name} has already boarded")


class BookingService:
    """Looks after passengers, bookings, check-in and boarding."""

    def __init__(self, flight_service):
        self.flight_service = flight_service
        self.passengers = {}
        self.bookings = {}
        self.boarding_rules = [MustBeCheckedIn(), BoardingMustBeOpen(), NotAlreadyBoarded()]

    # ---- passengers ----

    def add_passenger(self, name, email=""):
        if not name.strip():
            raise AirportError("A passenger needs a name")
        passenger_id = f"P{len(self.passengers) + 1:03d}"
        passenger = Passenger(passenger_id, name.strip(), email)
        self.passengers[passenger_id] = passenger
        return passenger

    def get_passenger(self, passenger_id):
        passenger = self.passengers.get(passenger_id.upper())
        if passenger is None:
            raise AirportError(f"There is no passenger {passenger_id.upper()}")
        return passenger

    # ---- bookings ----

    def book(self, passenger_id, flight_number):
        passenger = self.get_passenger(passenger_id)
        flight = self.flight_service.get_flight(flight_number)

        if not flight.is_open():
            raise AirportError(f"{flight.number} is {flight.status} and can't be booked")

        current = self.bookings_for_flight(flight.number)
        if len(current) >= flight.capacity:
            raise AirportError(f"{flight.number} is full")
        if any(b.passenger is passenger for b in current):
            raise AirportError(f"{passenger.name} is already booked on {flight.number}")

        reference = f"BK{len(self.bookings) + 1:03d}"
        booking = Booking(reference, passenger, flight)
        self.bookings[reference] = booking
        return booking

    def get_booking(self, reference):
        booking = self.bookings.get(reference.upper())
        if booking is None:
            raise AirportError(f"There is no booking {reference.upper()}")
        return booking

    def bookings_for_flight(self, flight_number):
        return [b for b in self.bookings.values() if b.flight.number == flight_number]

    def seats_left(self, flight):
        return flight.capacity - len(self.bookings_for_flight(flight.number))

    # ---- check-in and boarding ----

    def check_in(self, reference, now=None):
        now = now or datetime.now()
        booking = self.get_booking(reference)
        flight = booking.flight
        if booking.checked_in:
            raise AirportError("This passenger has already checked in")
        if not flight.is_open():
            raise AirportError(f"{flight.number} is {flight.status}, check-in is not possible")

        minutes = AirportSettings().checkin_closes_minutes
        if now > flight.departure - timedelta(minutes=minutes):
            raise AirportError(f"Check-in for {flight.number} closes {minutes} minutes before departure")

        booking.seat = self.next_free_seat(flight)
        booking.checked_in = True
        return booking

    def next_free_seat(self, flight):
        taken = {b.seat for b in self.bookings_for_flight(flight.number) if b.seat}
        # one row at a time: 1A 1B ... 1F, 2A ...
        letters = AirportSettings().seat_letters
        for row in range(1, flight.capacity // len(letters) + 2):
            for letter in letters:
                seat = f"{row}{letter}"
                if seat not in taken:
                    return seat

    def board(self, reference):
        booking = self.get_booking(reference)
        for rule in self.boarding_rules:
            rule.check(booking, booking.flight)
        booking.boarded = True
        return booking
