# Airport Management System (BCS 305)

A small standalone Python prototype for our Software Architecture project. It uses only the standard library, so there is nothing to install (Python 3.8 or newer).

## How to run

```bash
python main.py          # interactive menu
python main.py demo     # short scripted walkthrough (good for the presentation)
python tests.py         # run the tests
```

The program starts with 3 gates (A1, A2, B1) and 3 flights (EK201 has only 4 seats, so it is easy to test a full flight).

## What it does

| Area | Features |
|---|---|
| Flights | add a flight, view flights, change flight status |
| Gates | add a gate, assign a gate to a flight |
| Passengers | add a passenger, book them on a flight, refuse the booking if the flight is full |
| Check-in and boarding | check a passenger in (they get a seat), board them only while the flight is "Boarding" |

Other rules that are enforced: check-in closes 60 minutes before departure (a setting), a cancelled or departed flight cannot be booked, a passenger cannot book the same flight twice, a gate can only serve one flight at a time, and a flight status can only change in the allowed order (see `ALLOWED_CHANGES` in `models.py`, it matches our state machine diagram).

## Files

```
AirportSystem/
├── models.py     Flight, Gate, Passenger, Booking (just data and small helper methods)
├── services.py   FlightService (flights + gates) and BookingService (bookings, check-in, boarding)
├── main.py       console menu and the demo
├── tests.py      unit tests
└── README.md
```

The dependencies only go one way: `main.py` uses `services.py`, which uses `models.py`.

## Design patterns

**Observer** (`FlightService.add_listener` in `services.py`)
Problem: when a flight changes status, other parts of the system want to know (a departure board, later maybe notifications), but `FlightService` should not have to know about them. Solution: other code registers a function with `add_listener`, and `FlightService` calls every registered function after a status change. In `main.py` the `departure_board` function is the listener. If a listener crashes, the status change still goes through (our availability tactic).

**Strategy** (`MustBeCheckedIn`, `BoardingMustBeOpen`, `NotAlreadyBoarded` in `services.py`)
Problem: boarding has several rules, and they will change over time (for example a passport check). Putting them all in one big `if` chain in `board()` would make it messy. Solution: every rule is its own small class with a `check()` method, and `BookingService` just loops over a list of rules. Adding or removing a rule means changing that list, not the `board()` method.

**Singleton** (`AirportSettings` in `services.py`)
Problem: some settings are used in several places (how many minutes before departure check-in closes, which seat letters each row has). If every service made its own copy, changing a setting in one place would not change it in the others. Solution: `AirportSettings()` always returns the same single object, so everyone reads the same values. Changing `AirportSettings().checkin_closes_minutes` changes the rule for the whole system (see `test_changing_settings_changes_the_rule` in `tests.py`).
