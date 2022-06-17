# module to hold information about dimensions

MIN = 3
MAX = 10

X, Y, Z = range(3)  # syntactic sugar for the first three dimensions

# all the planes where rotation is visible
planes = [(X, Y), (X, Z), (Y, Z)]

# labels for all dimensions
labels = ["X", "Y", "Z"]

# fill in the above lists for all dimensions
for dim in range(3, MAX):
    planes.append((X, dim))
    planes.append((Y, dim))
    labels.append(str(dim + 1))
