import os
from formula_generator import FormulaGenerator
from dimacs_coder import DimacsCoder
import typing as ty
from utils.html_writer import timetable_to_html
import subprocess
import pycosat

def test_pycosat(dimacs_str : str):
    dimacs_arr = [x.split(" ") for x in dimacs_str.strip().split("\n")[1:]]
    dimacs_arr = [[int(x) for x in y if int(x) != 0 ] for y in dimacs_arr]
    for s in pycosat.itersolve(dimacs_arr):
        print(s)
    #  r = pycosat.solve(dimacs_arr)
    #  print(r)

def main():

    #TODO razdvojiti prve i druge vezbe(ako postoje)

    fg = FormulaGenerator("test_input.txt")

    num_of_results = 0
    unsat_count = 0
    fg.code()
    c = DimacsCoder(fg.formula)
    dimacs_string = c.create_dimacs_string()
    #  test_pycosat(dimacs_string)
    
    while num_of_results < 100 and unsat_count < 100:
        dimacs_arr = [x.split(" ") for x in dimacs_string.strip().split("\n")[1:]]
        dimacs_arr = [[int(x) for x in y if int(x) != 0 ] for y in dimacs_arr]
        solutions = list(pycosat.itersolve(dimacs_arr))
        if len(solutions) == 0:
            fg.remove_unit()
            fg.code()
            c = DimacsCoder(fg.formula)
            dimacs_string = c.create_dimacs_string()
            unsat_count += 1
            print("unsat")
        else:
            print(f"sat with {len(solutions)} sols")
            for solution in solutions:
                res = c.decode_dimacs_string(solution)
                with open(f"output/result{num_of_results}.html", "w") as html_file:
                    html_file.writelines(timetable_to_html(res) )
                num_of_results+=1
#
#
   #   for s in :
        #  print(s)
#
if __name__ == "__main__":
    main()
