# main.py - console menu for the airport system
# Run it with:  python main.py        (menu)
#               python main.py demo   (quick scripted walkthrough)

import sys
from datetime import datetime, timedelta

from models import AirportError
from services import FlightService, BookingService

flight_service = FlightService()
booking_service = BookingService(flight_service)


def departure_board(flight, old_status):
    # this gets called by FlightService every time a status changes
    print(f"  [Departure board] {flight.number} to {flight.destination}: "
          f"{old_status} -> {flight.status}")


def load_sample_data():
    start = datetime.now().replace(minute=0, second=0, microsecond=0)
    for code in ("A1", "A2", "B1"):
        flight_service.add_gate(code)
    flight_service.add_flight("EK201", "DXB", "LHR", start + timedelta(hours=5), 4)
    flight_service.add_flight("EK202", "DXB", "JFK", start + timedelta(hours=7), 300)
    flight_service.add_flight("EK203", "DXB", "LHR", start + timedelta(hours=9), 300)


def ask(question, default=""):
    shown = f"{question} [{default}]: " if default else f"{question}: "
    return input(shown).strip() or default


# ---------- menu actions ----------

def add_flight():
    number = ask("Flight number")
    origin = ask("From (airport code)")
    destination = ask("To (airport code)")
    when = ask("Departure (YYYY-MM-DD HH:MM)")
    departure = datetime.strptime(when, "%Y-%m-%d %H:%M")
    capacity = int(ask("Number of seats"))
    flight = flight_service.add_flight(number, origin, destination, departure, capacity)
    print(f"Added flight {flight.number}.")


def view_flights():
    flights = flight_service.list_flights()
    if not flights:
        print("No flights yet.")
    for f in flights:
        gate = f.gate.code if f.gate else "-"
        print(f"  {f.number:<7} {f.origin}->{f.destination}  {f.departure:%d %b %H:%M}  "
              f"{f.status:<10} gate {gate:<3} seats left: {booking_service.seats_left(f)}")


def change_status():
    number = ask("Flight number")
    status = ask("New status (Scheduled/Boarding/Delayed/Cancelled/Departed)")
    flight_service.change_status(number, status)


def add_gate():
    gate = flight_service.add_gate(ask("Gate code"))
    print(f"Added gate {gate.code}.")


def assign_gate():
    number = ask("Flight number")
    code = ask("Gate code")
    flight_service.assign_gate(number, code)
    print(f"{number.upper()} is now at gate {code.upper()}.")


def add_passenger():
    name = ask("Passenger name")
    email = ask("Email (optional)")
    p = booking_service.add_passenger(name, email)
    print(f"Added {p.name}, passenger id {p.id}.")


def book_passenger():
    passenger_id = ask("Passenger id")
    number = ask("Flight number")
    b = booking_service.book(passenger_id, number)
    print(f"Booked! Reference {b.reference} ({b.passenger.name} on {b.flight.number}).")


def view_bookings():
    if not booking_service.bookings:
        print("No bookings yet.")
    for b in booking_service.bookings.values():
        print(f"  {b.reference}  {b.passenger.name:<15} {b.flight.number}  "
              f"seat {b.seat or '-':<3} {b.state()}")


def check_in():
    b = booking_service.check_in(ask("Booking reference"))
    gate = b.flight.gate.code if b.flight.gate else "not assigned yet"
    print(f"{b.passenger.name} is checked in. Seat {b.seat}, gate: {gate}.")


def board():
    b = booking_service.board(ask("Booking reference"))
    print(f"{b.passenger.name} has boarded {b.flight.number}.")


MENU = [
    ("Add flight", add_flight),
    ("View flights", view_flights),
    ("Change flight status", change_status),
    ("Add gate", add_gate),
    ("Assign gate to flight", assign_gate),
    ("Add passenger", add_passenger),
    ("Book passenger on a flight", book_passenger),
    ("View bookings", view_bookings),
    ("Check in passenger", check_in),
    ("Board passenger", board),
]


def run_menu():
    while True:
        print("\n=== Airport Management System ===")
        for number, (label, _) in enumerate(MENU, start=1):
            print(f"{number:>2}. {label}")
        print(" 0. Exit")

        choice = input("Choose: ").strip()
        if choice == "0":
            print("Bye!")
            break
        if not choice.isdigit() or not 1 <= int(choice) <= len(MENU):
            print("Please type one of the numbers above.")
            continue
        try:
            MENU[int(choice) - 1][1]()
        except (AirportError, ValueError) as error:
            print(f"Error: {error}")


# ---------- scripted demo ----------

def try_it(description, action, *args):
    # runs one step of the demo and shows the error if the rules say no
    try:
        result = action(*args)
        print(f"OK   - {description}")
        return result
    except AirportError as error:
        print(f"FAIL - {description}: {error}")


def run_demo():
    print("--- Booking ---")
    people = [booking_service.add_passenger(n) for n in ("Amina Khan", "Omar Saeed", "Layla Hassan",
                                                          "Yusuf Ali", "Sara Noor")]
    bookings = []
    for person in people:
        # EK201 only has 4 seats, so the 5th booking should be refused
        bookings.append(try_it(f"book {person.name} on EK201", booking_service.book, person.id, "EK201"))

    print("\n--- Check-in and boarding ---")
    amina = bookings[0]
    try_it("check in Amina", booking_service.check_in, amina.reference)
    print(f"     seat: {amina.seat}")
    try_it("board Amina too early", booking_service.board, amina.reference)
    try_it("assign gate A1 to EK201", flight_service.assign_gate, "EK201", "A1")
    try_it("set EK201 to Boarding", flight_service.change_status, "EK201", "Boarding")
    try_it("board Amina", booking_service.board, amina.reference)
    try_it("board Amina again", booking_service.board, amina.reference)

    print("\n--- Flights now ---")
    view_flights()


if __name__ == "__main__":
    flight_service.add_listener(departure_board)
    load_sample_data()
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo()
    else:
        run_menu()
