import unittest
from datetime import datetime, timedelta

from models import AirportError
from services import FlightService, BookingService, AirportSettings


class AirportTests(unittest.TestCase):
    def setUp(self):
        AirportSettings().reset()
        self.flights = FlightService()
        self.bookings = BookingService(self.flights)
        self.flights.add_flight("EK1", "DXB", "LHR", datetime.now() + timedelta(hours=3), 2)
        self.flights.add_gate("A1")
        self.flights.add_gate("A2")
        self.amina = self.bookings.add_passenger("Amina")
        self.omar = self.bookings.add_passenger("Omar")
        self.layla = self.bookings.add_passenger("Layla")

    def test_cannot_book_full_flight(self):
        self.bookings.book(self.amina.id, "EK1")
        self.bookings.book(self.omar.id, "EK1")
        with self.assertRaises(AirportError):
            self.bookings.book(self.layla.id, "EK1")

    def test_cannot_book_same_passenger_twice(self):
        self.bookings.book(self.amina.id, "EK1")
        with self.assertRaises(AirportError):
            self.bookings.book(self.amina.id, "EK1")

    def test_cannot_book_cancelled_flight(self):
        self.flights.change_status("EK1", "Cancelled")
        with self.assertRaises(AirportError):
            self.bookings.book(self.amina.id, "EK1")

    def test_bad_status_change(self):
        self.flights.change_status("EK1", "Cancelled")
        with self.assertRaises(AirportError):
            self.flights.change_status("EK1", "Boarding")

    def test_gate_belongs_to_one_flight(self):
        self.flights.add_flight("EK2", "DXB", "JFK", datetime.now() + timedelta(hours=4), 10)
        self.flights.assign_gate("EK1", "A1")
        with self.assertRaises(AirportError):
            self.flights.assign_gate("EK2", "A1")

    def test_moving_gate_frees_the_old_one(self):
        self.flights.assign_gate("EK1", "A1")
        self.flights.assign_gate("EK1", "A2")
        self.assertIsNone(self.flights.gates["A1"].flight)

    def test_gate_released_when_cancelled(self):
        self.flights.assign_gate("EK1", "A1")
        self.flights.change_status("EK1", "Cancelled")
        self.assertIsNone(self.flights.gates["A1"].flight)

    def test_check_in_gives_different_seats(self):
        a = self.bookings.book(self.amina.id, "EK1")
        b = self.bookings.book(self.omar.id, "EK1")
        self.bookings.check_in(a.reference)
        self.bookings.check_in(b.reference)
        self.assertNotEqual(a.seat, b.seat)

    def test_boarding_rules(self):
        b = self.bookings.book(self.amina.id, "EK1")
        with self.assertRaises(AirportError):   # not checked in
            self.bookings.board(b.reference)
        self.bookings.check_in(b.reference)
        with self.assertRaises(AirportError):   # flight not boarding yet
            self.bookings.board(b.reference)
        self.flights.change_status("EK1", "Boarding")
        self.bookings.board(b.reference)
        self.assertTrue(b.boarded)
        with self.assertRaises(AirportError):   # already on the plane
            self.bookings.board(b.reference)

    def test_listener_hears_status_change(self):
        heard = []
        self.flights.add_listener(lambda flight, old: heard.append((flight.number, old)))
        self.flights.change_status("EK1", "Delayed")
        self.assertEqual(heard, [("EK1", "Scheduled")])

    def test_broken_listener_does_not_block_status_change(self):
        def broken(flight, old):
            raise RuntimeError("oops")
        self.flights.add_listener(broken)
        self.flights.change_status("EK1", "Delayed")
        self.assertEqual(self.flights.get_flight("EK1").status, "Delayed")

    def test_settings_is_a_singleton(self):
        self.assertIs(AirportSettings(), AirportSettings())

    def test_check_in_closes_before_departure(self):
        b = self.bookings.book(self.amina.id, "EK1")
        late = self.flights.get_flight("EK1").departure - timedelta(minutes=30)
        with self.assertRaises(AirportError):
            self.bookings.check_in(b.reference, now=late)

    def test_changing_settings_changes_the_rule(self):
        AirportSettings().checkin_closes_minutes = 10   # same object everyone uses
        b = self.bookings.book(self.amina.id, "EK1")
        late = self.flights.get_flight("EK1").departure - timedelta(minutes=30)
        self.bookings.check_in(b.reference, now=late)   # allowed now
        self.assertTrue(b.checked_in)


if __name__ == "__main__":
    unittest.main()
