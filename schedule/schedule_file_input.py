from logilab.constraint import *
from csv import reader, writer
from time import strftime

DEBUGGING = True
worker_names = {0: "Yotam", 1: "Guy", 2: "Roman", 3: "Sagi", 4: "Vitaly", 5: "Gal", 6: "Empty"}
worker_nums = {"Yotam": 0, "Guy": 1, "Roman": 2, "Sagi": 3, "Vitaly": 4, "Gal": 5, "Empty": 6}


def shift_list_to_dictionary(shift_list):
    shift_d = {}
    for shift in shift_list:
        day_and_shift = shift_to_string(shift[0:2])
        if day_and_shift not in shift_d:
            shift_d[day_and_shift] = shift[2]
        else:
            shift_d[day_and_shift] = max(shift_d[day_and_shift], shift[2])
    return shift_d


def extend_overlapping_shifts_to_be_unique(nonunique_overlap, shift_list):
    unique_overlap_list = []

    shift_d = shift_list_to_dictionary(shift_list)

    for pair in nonunique_overlap:
        if not ((pair[0] in shift_d) and (pair[1] in shift_d)):
            raise ValueError

        for i in range(shift_d[pair[0]] + 1):
            for j in range(shift_d[pair[1]] + 1):
                unique_overlap_list.append(
                    (extend_shift_key(pair[0], i),
                     extend_shift_key(pair[1], j)))

    return unique_overlap_list


def load_overlapping_shifts(file_path):
    overlap_list = []
    for line in open(file_path, 'r').readlines():
        if line[0] == "%":
            break
        elif line[0] == "#":
            continue
        (day_0, shift_0, day_1, shift_1) = line.split(',')

        overlap_list.append((shift_to_string([int(day_0),
                                              int(shift_0)]),
                             shift_to_string([int(day_1),
                                              int(shift_1)])))
    return overlap_list


def load_workers():
    with open("people.csv", "r") as csvfile:
        worker_list = []
        name = ""
        for line in reader(csvfile):
            if line[0] == "END":
                break
            elif line[0] == "":
                name = ""
                continue
            elif len(line[0]) > 2:
                name = line[0]
                continue
            else:
                for i in range(1, 4):
                    worker_list.append([worker_nums[name], int(line[0]), i, int(line[i])])

    return worker_list


def load_worker_jobs(file_path):
    worker_job_list = []
    worker_job_file = open(file_path, 'r')
    worker_job_lines = worker_job_file.readlines()
    for line in worker_job_lines:
        if line[0] == "%":
            break
        elif line[0] == "#":
            continue
        (worker, job) = line.split(',')
        worker_job_list.append([int(worker), int(job), ])

    return worker_job_list


def load_shift_jobs(file_path):
    shift_job_list = []
    shift_job_file = open(file_path, 'r')
    shift_job_lines = shift_job_file.readlines()
    for line in shift_job_lines:
        if line[0] == "%":
            break
        elif line[0] == "#":
            continue
        (day, shift, job, number) = line.split(',')
        shift_job_list.append([int(day), int(shift), int(job), int(number)])

    return shift_job_list


def shift_to_string(shift):
    string_representation = 'd' + str(shift[0]) + 's' + str(shift[1])
    return string_representation


def unique_shift_to_string(shift):
    string_representation = 'd' + str(shift[0]) + 's' + str(shift[1]) + 'n' + str(shift[2])
    return string_representation


def worker_to_string(worker_number):
    string_representation = worker_names[worker_number]
    return string_representation


def shift_job_to_string_list(shift_job_item, worker_number):
    string_worker = 'd' + str(shift_job_item[0]) + 's' + str(shift_job_item[1]) + 'n' + str(worker_number)
    string_job = str(shift_job_item[2])
    return [string_worker, string_job]


def shorten_shift_key(key):
    split_key = key.split('n')
    return split_key[0]


def extend_shift_key(key, shift_number):
    return key + 'n' + str(shift_number)


def make_shift_tuple(shift_list):
    shifts = ()
    for shift in shift_list:
        string_representation = unique_shift_to_string(shift)

        shifts = shifts + (string_representation,)

    return shifts


def make_worker_tuple(worker_list):
    worker_numbers = []
    for item in worker_list:
        worker_numbers.append(item[0])

    number_of_workers = len(set(worker_numbers))

    workers = ()
    for worker_num in range(number_of_workers):
        string_representation = worker_to_string(worker_num)
        workers = workers + (string_representation,)
    print(workers)
    return workers


def make_shift_job_tuple(shift_job_list):
    shift_jobs = ()
    for item in shift_job_list:
        num_workers = item[3]
        for x in range(0, num_workers):
            string_representation = shift_job_to_string_list(item, x)
            shift_jobs = shift_jobs + (string_representation,)

    return shift_jobs


def make_shift_domains(shift_list, workers_tuple):
    domains = {}
    for shift in shift_list:
        # Get the possible values for this shift
        values = [('d' + str(shift[0]), 's' + str(shift[1]), worker)
                  for worker in workers_tuple]

        shift_string = unique_shift_to_string(shift)
        domains[shift_string] = fd.FiniteDomain(values)
    return domains


def make_worker_prefs(worker_list):
    worker_prefs = {}
    for item in worker_list:
        shift = shift_to_string([item[1], item[2]])
        worker = worker_to_string(item[0])
        key = worker + shift
        worker_prefs[key] = item[3]

    return worker_prefs


def make_overlapping_constraints(constraints, overlap_list):
    for shift_pair in overlap_list:
        constraints.append(fd.make_expression(
            shift_pair, "%(shift_0)s[2] != %(shift_1)s[2]" %
                        {'shift_0': shift_pair[0], "shift_1": shift_pair[1]}))

    return constraints


def make_availability_constraints(constraints, shift_tuple, worker_tuple, worker_prefs, availability_threshold):
    for worker in worker_tuple:
        for shift in shift_tuple:
            short_key = shorten_shift_key(shift)
            key = worker + short_key
            if worker_prefs[key] < availability_threshold:
                constraints.append(fd.make_expression(
                    (shift,), "%(a_shift)s[2] != '%(worker)s'" %
                              {'a_shift': shift, "worker": worker}))

    return constraints


def make_job_constraints(constraints, worker_job_list, shift_job_tuple):
    for shift_job in shift_job_tuple:
        for worker_job in worker_job_list:
            if int(shift_job[1]) != worker_job[1]:
                shift_key = shift_job[0]
                worker = 'w' + str(worker_job[0])
                constraints.append(fd.make_expression(
                    (shift_key,), "%(a_shift)s[2] != '%(a_worker)s'" %
                                  {'a_shift': shift_key, "a_worker": worker}))
    return constraints


def cost_function(**kwargs):
    global worker_prefs
    score = 0

    worker_and_shift_l = []
    for key in kwargs:
        short_key = shorten_shift_key(key)
        worker_and_shift_l.append(str(kwargs[key][2]) + str(short_key))

    for constraint in worker_prefs:
        if constraint in worker_and_shift_l:
            score += worker_prefs[constraint]

    return score


def csvprint(solution, i):
    list_to_print = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]
    with open("schedule(%d).csv" % i, "w+") as csvfile:
        write_to = writer(csvfile)

        for key in solution:
            threeplet = solution[key]
            list_to_print[int(threeplet[1][1:]) - 1][int(threeplet[0][1:]) - 1] = threeplet[2]

        for line in list_to_print:
            write_to.writerow(line)
    print("DONE")


def main():
    global worker_prefs
    availability_threshold = 100
    shift_list = [[i, j, 0] for i in range(1, 32) for j in range(1, 4)]
    worker_list = load_workers()
    for i in range(1, 32):
        for j in range(1, 4):
            worker_list.append([6, i, j, 0.5])
    shift_tuple = make_shift_tuple(shift_list)
    worker_tuple = make_worker_tuple(worker_list)
    worker_prefs = make_worker_prefs(worker_list)
    solutions = []
    while len(solutions) < 1:
        if DEBUGGING:
            print(strftime('%H:%M:%S') + ": Availability: " + str(availability_threshold))

        domains = make_shift_domains(shift_list, worker_tuple)
        constraints = []
        constraints = make_availability_constraints(constraints,
                                                    shift_tuple,
                                                    worker_tuple,
                                                    worker_prefs,
                                                    availability_threshold)

        availability_threshold -= 1
        if availability_threshold == 0:
            availability_threshold = 0.5

        constraints.append(fd.AllDistinct(shift_tuple))

        r = Repository(shift_tuple, domains, constraints)

        # for s in Solver().solve_best(r, cost_function, 0):
        #    solutions.append(s)
        solutions.append(Solver().solve_one(r, 1))
        if solutions[0] is None:
            solutions = []
    print("Found", len(solutions), "solutions.")
    print("\n\nHere's the best solution we found:")

    # I will print this to a csv file:
    for i in range(len(solutions)):
        csvprint(solutions[-1], i)


main()
