"""
Make this a function:
Input values: num_for_loops, lines, filename
Output value: num_while_loops
(NB: "Output" doesn't mean "stuff we print")
"""

def main():
    """
    Main function. Read file. Count required attributes
    :return:
    """

    filename = input("Enter program filename: ")
    lines = open(filename).readlines()
    num_for_loops = 0

    for line in lines:
        if line.strip().startswith("for"):
            num_for_loops += 1

    print("Program {} contain {} for loops".format(filename, num_for_loops))

    num_while_loops = 0
    for line in lines:
        if line.strip().startswith("while"):
            num_while_loops += 1

    print("Program {} contain {} for loops".format(filename, num_while_loops))

    num_if_loops = 0
    for line in lines:
        if line.strip().startswith("if"):
            num_if_loops += 1

    print("Program {} contain {} for loops".format(filename, num_if_loops))