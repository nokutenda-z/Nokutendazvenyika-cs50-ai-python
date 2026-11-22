import sys
from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create a new CSP crossword generator.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return a 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print the crossword assignment nicely to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save the crossword assignment as an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, then solve the CSP using backtracking.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Remove any values from a variable's domain that violate its unary
        constraints (i.e., words whose length doesn't match the variable's length).[span_3](start_span)[span_3](end_span)
        """
        for var in self.crossword.variables:
            # Keep only words that match the required length of the variable
            self.domains[var] = {
                word for word in self.domains[var]
                if len(word) == var.length
            }

    def revise(self, x, y):
        """
        Make variable `x` arc-consistent with variable `y` by removing values
        from `x`'s domain that have no corresponding matching value in `y`'s domain.[span_4](start_span)[span_4](end_span)[span_5](start_span)[span_5](end_span)
        """
        revised = False
        overlap = self.crossword.overlaps[x, y]

        # If there is no overlap between x and y, nothing to revise
        if overlap is None:
            return False

        i, j = overlap
        values_to_remove = set()

        # Check every word in x's domain for a valid partner in y's domain
        for x_val in self.domains[x]:
            match_found = any(x_val[i] == y_val[j] for y_val in self.domains[y])
            if not match_found:
                values_to_remove.add(x_val)

        # If we found unsupported words, remove them and mark as revised
        if values_to_remove:
            self.domains[x] -= values_to_remove
            revised = True

        return revised

    def ac3(self, arcs=None):
        """
        Enforce arc consistency across the problem using the AC3 algorithm.[span_6](start_span)[span_6](end_span)
        """
        # If no initial arcs are provided, start with all variable-neighbor pairs
        if arcs is None:
            queue = [
                (x, y)
                for x in self.crossword.variables
                for y in self.crossword.neighbors(x)
            ]
        else:
            queue = list(arcs)

        while queue:
            x, y = queue.pop(0)

            if self.revise(x, y):
                # If a domain becomes empty, no solution is possible
                if len(self.domains[x]) == 0:
                    return False

                # Re-check affected neighboring arcs (excluding y)
                for z in self.crossword.neighbors(x) - {y}:
                    queue.append((z, x))

        return True

    def assignment_complete(self, assignment):
        """
        Return True if all crossword variables have been assigned a value.[span_7](start_span)[span_7](end_span)
        """
        return (
                set(assignment.keys()) == self.crossword.variables and
                all(assignment[var] is not None for var in self.crossword.variables)
        )

    def consistent(self, assignment):
        """
        Check if the current assignment satisfies all unary and binary constraints:
          1. All assigned words are unique (no duplicates).
          2. Words match their required length.
          3. Overlapping characters between neighboring variables match.[span_8](start_span)[span_8](end_span)
        """
        # Ensure all assigned words are completely distinct
        assigned_words = list(assignment.values())
        if len(assigned_words) != len(set(assigned_words)):
            return False

        for var, word in assignment.items():
            # Check length constraint
            if len(word) != var.length:
                return False

            # Check consistency with already assigned neighbors
            for neighbor in self.crossword.neighbors(var):
                if neighbor in assignment:
                    overlap = self.crossword.overlaps[var, neighbor]
                    if overlap is not None:
                        i, j = overlap
                        if word[i] != assignment[neighbor][j]:
                            return False

        return True

    def order_domain_values(self, var, assignment):
        """
        Order values in `var`'s domain using the Least-Constraining Value (LCV) heuristic:
        The value that rules out the fewest choices for neighboring variables comes first.[span_9](start_span)[span_9](end_span)
        """

        def count_ruled_out_values(val):
            ruled_out_count = 0
            for neighbor in self.crossword.neighbors(var):
                if neighbor not in assignment:
                    overlap = self.crossword.overlaps[var, neighbor]
                    if overlap is not None:
                        i, j = overlap
                        for neighbor_val in self.domains[neighbor]:
                            if val[i] != neighbor_val[j]:
                                ruled_out_count += 1
            return ruled_out_count

        return sorted(list(self.domains[var]), key=count_ruled_out_values)

    def select_unassigned_variable(self, assignment):
        """
        Select the next variable to assign using the Minimum Remaining Values (MRV)
        heuristic, breaking ties with the Degree heuristic.[span_10](start_span)[span_10](end_span)
        """
        unassigned_vars = [v for v in self.crossword.variables if v not in assignment]

        # Sort by: 1) fewest remaining values in domain (ascending), 2) highest degree (descending)[span_11](start_span)[span_11](end_span)
        unassigned_vars.sort(
            key=lambda v: (len(self.domains[v]), -len(self.crossword.neighbors(v)))
        )

        return unassigned_vars[0] if unassigned_vars else None

    def backtrack(self, assignment):
        """
        Use backtracking search to find a complete and consistent crossword assignment.[span_12](start_span)[span_12](end_span)
        """
        if self.assignment_complete(assignment):
            return assignment

        var = self.select_unassigned_variable(assignment)

        for value in self.order_domain_values(var, assignment):
            assignment[var] = value

            if self.consistent(assignment):
                result = self.backtrack(assignment)
                if result is not None:
                    return result

            # Undo assignment if it leads to a dead end
            del assignment[var]

        return None


def main():
    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()