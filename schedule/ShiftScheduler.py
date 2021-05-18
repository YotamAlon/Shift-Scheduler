from csv import reader, writer
from datetime import datetime
from calendar import monthrange
from logilab.constraint.fd import FiniteDomain, AllDistinct, make_expression
from logilab.constraint import Repository, Solver


class ShiftScheduler(object):
    def __init__(self, shifts_per_day=3, days_in_month=None):
        if days_in_month is None:
            days_in_month = self.default_days_in_month

        # shift_list = [[i, j, 0] for i in range(1, 32) for j in range(1, 4)]
        self.shift_list = [Shift(day=i, number=j) for i in range(days_in_month) for j in range(shifts_per_day)]
        self.csv_file_name = "people.csv"
        self.availability_threshold = 100
        self.employee_list = []

    def create_schedule(self):
        worker_list = self.load_workers()
        shift_tuple = self.make_shift_tuple()
        worker_tuple = self.make_worker_tuple()
        worker_prefs = self.make_worker_prefs(worker_list)
        domains = self.make_shift_domains(worker_tuple)
        solutions = []
        while len(solutions) < 1:
            # if DEBUGGING:
            #     print(strftime('%H:%M:%S') + ": Availability: " + str(availability_threshold))

            constraints = self.make_availability_constraints(worker_tuple, worker_prefs)

            self.availability_threshold -= 1
            if self.availability_threshold == 0:
                self.availability_threshold = 0.5

            constraints.append(AllDistinct(tuple([shift.to_string() for shift in self.shift_list])))

            r = Repository(tuple([shift.to_string() for shift in self.shift_list]), domains, constraints)

            # for s in Solver().solve_best(r, cost_function, 0):
            #    solutions.append(s)
            solutions.append(Solver().solve_one(r, 1))
            if solutions[0] is None:
                solutions = []

    def make_shift_tuple(self):
        return tuple([shift.to_string() for shift in self.shift_list])

    def make_worker_tuple(self):
        return tuple([employee.name for employee in self.employee_list])

    def make_worker_prefs(self, worker_list):
        worker_prefs = {}
        for employee_shift_pref in worker_list:
            shift_str = employee_shift_pref.shift.to_string(unique=False)
            worker = employee_shift_pref.employee.name
            key = worker + shift_str
            worker_prefs[key] = employee_shift_pref.pref

        return worker_prefs

    def make_shift_domains(self, workers_tuple):
        domains = {}
        for shift in self.shift_list:
            # Get the possible values for this shift
            values = [(shift.to_string(unique=False), worker) for worker in workers_tuple]

            shift_string = shift.to_string()
            domains[shift_string] = FiniteDomain(values)
        return domains

    def make_availability_constraints(self, worker_tuple, worker_prefs):
        constraints = []
        for worker in worker_tuple:
            for shift in self.shift_list:
                short_key = shift.to_string(unique=False)
                key = worker + short_key
                if worker_prefs[key] < self.availability_threshold:
                    constraints.append(make_expression(
                        (shift.to_string(),), "%(a_shift)s[2] != '%(worker)s'" % {'a_shift': shift.to_string(), "worker": worker}))

        return constraints

    def load_workers(self):
        with open(self.csv_file_name, 'r') as csvfile:
            worker_list = []
            for line in reader(csvfile):
                if line[0] == "END":
                    break
                elif line[0] == "":
                    continue
                elif len(line[0]) > 2:
                    self.employee_list.append(Employee(name=line[0], number=len(self.employee_list)))
                    continue
                else:
                    for i in range(1, 4):
                        worker_list.append(EmployeeShiftPref(employee=self.employee_list[-1],
                                                             shift=self.get_shift(int(line[0]), i),
                                                             pref=int(line[i])))

        return worker_list

    @property
    def default_days_in_month(self):
        print('Taking days from next month')
        now = datetime.now()
        return monthrange(now.year, now.month + 1)[1]

    def get_shift(self, day, number):
        for shift in self.shift_list:
            if shift.day == day and shift.number == number:
                return shift
        return None


class Shift(object):
    def __init__(self, day, number, employee=None):
        self.day = day
        self.number = number
        self.employee = employee

    def to_string(self, unique=True):
        return 'd' + str(self.day) + 's' + str(self.number) + ('n' + str(0) if unique else '')


class Employee(object):
    def __init__(self, name, number):
        self.name = name
        self.number = number


class EmployeeShiftPref(object):
    def __init__(self, employee, shift, pref):
        self.employee = employee
        self.shift = shift
        self.pref = pref