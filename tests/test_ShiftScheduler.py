import unittest


class TestSchedulerRun(unittest.TestCase):
    def test_complete_flow(self):
        from schedule.ShiftScheduler import ShiftScheduler
        scheduler = ShiftScheduler(shifts_per_day=3, days_in_month=31)
        scheduler.create_schedule()


if __name__ == '__main__':
    unittest.main()
