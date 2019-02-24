import os
from formula_generator import FormulaGenerator
from dimacs_coder import DimacsCoder
import typing as ty
from utils.html_writer import timetable_to_html
import subprocess

def main():

    #TODO razdvojiti prve i druge vezbe(ako postoje)

    fg = FormulaGenerator("test_input.txt")

    num_of_results = 0
    unsat_count = 0
    fg.code()
    c = DimacsCoder(fg.formula)
    dimacs_string = c.create_dimacs_string()
    FNULL = open(os.devnull, 'w')
    while True:
        if unsat_count > 1000 or num_of_results > 100:
            break
        dimacs_in = open("out.cnf", "w")
        dimacs_out = open("solution.cnf", "r")

        dimacs_in.writelines(dimacs_string)
        dimacs_in.flush()

        subprocess.run(["minisat", "out.cnf", "solution.cnf"], stdout = FNULL)
        dimacs_in.close()

        is_solved = dimacs_out.readline().strip() == "SAT"
        if is_solved:
            solution = dimacs_out.readline()
            solution = solution.split(" ")
            solution = solution[:-1] #all but last 0
            res = c.decode_dimacs_string(solution)
            with open(f"output/result{num_of_results}.html", "w") as html_file:
                html_file.writelines(timetable_to_html(res) )

            num_of_results += 1

            #increase number of clauses
            tmp = dimacs_string.split("\n")
            num_of_clauses = int(tmp[0].split(" ")[-1]) + 1
            num_of_vars = int(tmp[0].split(" ")[2])
            dimacs_string = f"p cnf {num_of_vars} {num_of_clauses}\n" + "\n".join(tmp[1:])

            #we forbid current solution so we get other combinations
            tmp : str = ''
            for s in solution:
                if s[0] == '-':#if negated
                    tmp += s[1:] + ' '#then add positive
                else: #else add negated
                    tmp += '-' + s + ' '
            
            dimacs_string += tmp + '0\n'
        else:
            fg.remove_unit()
            fg.code()
            c = DimacsCoder(fg.formula)
            dimacs_string = c.create_dimacs_string()
            unsat_count += 1
            print("UNSAT")
        dimacs_out.close()

if __name__ == "__main__":
    main()
