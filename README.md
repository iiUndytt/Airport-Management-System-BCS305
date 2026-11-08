# Airport Management System

This project is an Airport Management System created for Software Architecture BCS 305.

System will be used to control flight, airport gates, passengers, bookings etc. It is further essential to allow travellers to sign in/up and get on-board their aircraft as well as ensuring that the basic rules in the airport are adhered to.

## Main Features

- Add and view flights.
- Change flight statuses.
Create gates and attach them to flights.
- Register passengers.
- Make bookings for space on available-flying aircraft.
- Deny bookings when full flight.
- Check in passengers and assign seats.
- Be attentive to all passengers when the boarding door is open.
- Show the states of flights.

## Project Structure

- `models.py` – Contains the main classes: Flight, Gate, Passenger, and Booking.
The flight management system, gate assignments, booking and check-in/boarding will be managed from a "services.py".
- `main.py` – Main Menu and demonstration.
- `tests.py` – Test file for testing the functionality of the system.

## Design Patterns

The project is designed based on the following three patterns:

**1. Observer Pattern**

Used to notify other parts of the system whenever a flight's status changes. An example of this is if a flight is timed down, the departure board updates.

**2. Strategy Pattern**

Used for boarding validation purposes. Conditionals, such as passenger check-in and the open nature of the boarding are checked one by one.

**3. Singleton Pattern**

For use in the airport environment. It ensures that only a single configuration object is shared across the system and not multiple copies.

## How to Run

Ensure that Python 3.8+ is installed.

From the project folder execute the following commands:

Begin the interact menu:

```bash
python main.py
```

Run the demonstration:

```bash
python main.py demo
```

Run the tests:

```bash
python tests.py
```

## Notes

The system includes, with samples of wings and gates, to enable to features to be readily tested by the system.

The project will be made a small working prototype exhibiting basic aspects of the airport operations and software architecture.
