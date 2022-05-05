# module to hold information about dimensions

MAX = 10

# all the planes where rotation is visible
planes = [(0, 1), (0, 2), (1, 2)]

# labels for all dimensions
labels = ['X', 'Y', 'Z']

# fill in the above lists for all dimensions
for dim in range(3, MAX):
    planes.append((0, dim))
    planes.append((1, dim))
    labels.append(str(dim + 1))
