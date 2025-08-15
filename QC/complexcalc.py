import matplotlib.pyplot as plt

def get_cmplx_no():
    cmplx_no = input(f"Enter a Complex Number:")
    return complex(cmplx_no)

def cmplx_add (cmplx_no1,cmplx_no2):
    """Add complex numbers (cmplx_no1 = a + bi, cmplx_no2 = c + di)."""
    # (a + bi) + (c + di) = (a + c) + (b + d)i
    real_no = cmplx_no1.real + cmplx_no2.real
    imag_no = cmplx_no1.imag + cmplx_no2.imag

    return complex(real_no, imag_no)

def cmplx_multiply (cmplx_no1,cmplx_no2):
    """Multiply  complex numbers (cmplx_no1 = a + bi, cmplx_no2 = c + di)."""
    # (a + bi) * (c + di) = (ac - bd) + (ad + bc)i
    real_part = (cmplx_no1.real * cmplx_no2.real) - (cmplx_no1.imag * cmplx_no2.imag)
    imag_part = (cmplx_no1.real * cmplx_no2.imag) + (cmplx_no1.imag * cmplx_no2.real)
    return complex(real_part, imag_part)

def cmplx_minus (cmplx_no1, cmplx_no2):
    """Subtract complex numbers (cmplx_no1 = a + bi, cmplx_no2 = c + di)."""
    # (a + bi) - (c + di) = (a - c) + (b - d)i
    real_part = cmplx_no1.real - cmplx_no2.real
    imag_part = cmplx_no1.imag - cmplx_no2.imag
    return complex(real_part, imag_part)

def cmplx_divide(cmplx_no1, cmplx_no2):
    """Divides two complex numbers (z1 = a + bi, z2 = c + di). Handles division by zero."""
    # (a + bi) / (c + di) = [(ac + bd) / (c^2 + d^2)] + [(bc - ad) / (c^2 + d^2)]i
    cmplx_no2_squared = (cmplx_no2.real**2 + cmplx_no2.imag**2)

    if cmplx_no2_squared == 0:
        return "Cannot divide by zero!"

    real_part = ((cmplx_no1.real * cmplx_no2.real) + (cmplx_no1.imag * cmplx_no2.imag)) / cmplx_no2_squared
    imag_part = ((cmplx_no1.imag * cmplx_no2.real) - (cmplx_no1.real * cmplx_no2.imag)) / cmplx_no2_squared
    return complex(real_part, imag_part)

def plot_cmplx_no(cmplx_no, titles):
    """
    Prints a list of complex numbers and their coordinates, simulating a text-based plot.
    
    Args:
        complex_numbers (list): A list of complex numbers.
        titles (list): A list of titles for each complex number.
    """
    print("\n--- Complex Number Coordinates ---")
    print("{:<15} {:<10} {:<10}".format("Title", "Real (X)", "Imaginary (Y)"))
    print("-" * 45)
    for i, z in enumerate(cmplx_no):
        # Extract real and imaginary parts
        x = z.real
        y = z.imag
        print("{:<15} {:<10.2f} {:<10.2f}".format(titles[i], x, y))
    print("----------------------------------\n")

    plt.figure(figsize=(8, 8))
    for i, z in enumerate(cmplx_no):
        # Extract real and imaginary parts
        x = z.real
        y = z.imag
        # Plot the point
        plt.plot(x, y, 'o', label=f'{titles[i]}: ({x:.2f} + {y:.2f}j)')
        # Add annotation
        plt.annotate(titles[i], (x, y), textcoords="offset points", xytext=(5,5), ha='center')

    plt.xlabel("Real Axis")
    plt.ylabel("Imaginary Axis")
    plt.title("Complex Number Operations")
    plt.grid(True)
    plt.axhline(0, color='black',linewidth=0.5)
    plt.axvline(0, color='black',linewidth=0.5)
    plt.legend()
    plt.show()  


def main():
    cmplx_no1=get_cmplx_no()
    cmplx_no2=get_cmplx_no()
    cmplx_sum=cmplx_add(cmplx_no1,cmplx_no2)
    cmplx_product=cmplx_multiply(cmplx_no1,cmplx_no2)
    cmplx_diff=cmplx_minus(cmplx_no1,cmplx_no2)
    cmplx_quotient=cmplx_divide(cmplx_no1,cmplx_no2)

    print(cmplx_no1,cmplx_no2,cmplx_sum,cmplx_product,cmplx_diff,cmplx_quotient)

    cmplx_to_plot = [cmplx_no1, cmplx_no2, cmplx_sum, cmplx_product, cmplx_diff, cmplx_quotient]
    titles_for_plot = ["cmplx_no1", "cmplx_no2", "cmplx_no1 + cmplx_no2", "cmplx_no1 * cmplx_no2", "cmplx_no1 - cmplx_no2", "cmplx_no1 / cmplx_no2"]

    # Plot the results
    plot_cmplx_no(cmplx_to_plot, titles_for_plot)

if __name__ == "__main__":
    main()