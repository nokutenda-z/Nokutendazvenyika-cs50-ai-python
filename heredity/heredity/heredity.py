import csv
import itertools
import sys

# Global probability tables provided by the project specification
PROBS = {
    # Unconditional probabilities for having the gene
    "gene": {
        2: 0.01,
        1: 0.03,
        0: 0.96
    },

    # Probability of exhibiting the trait based on gene count
    "trait": {
        2: {True: 0.65, False: 0.35},
        1: {True: 0.56, False: 0.44},
        0: {True: 0.01, False: 0.99}
    },

    # Chance of a gene mutating during transmission
    "mutation": 0.01
}


def main():
    # Make sure the user provided a data file as a command-line argument
    if len(sys.argv) != 2:
        sys.exit("Usage: python heredity.py data.csv")

    people = load_data(sys.argv[1])

    # Initialize a dictionary to track accumulated probabilities for each person
    probabilities = {
        person: {
            "gene": {2: 0, 1: 0, 0: 0},
            "trait": {True: 0, False: 0}
        }
        for person in people
    }

    names = set(people)

    # Evaluate every possible combination of people who might have the trait
    for have_trait in powerset(names):

        # Skip this combination if it conflicts with known evidence in the CSV
        fails_evidence = any(
            (people[person]["trait"] is not None and
             people[person]["trait"] != (person in have_trait))
            for person in names
        )
        if fails_evidence:
            continue

        # Evaluate every possible combination of gene counts across the family
        for one_gene in powerset(names):
            for two_genes in powerset(names - one_gene):
                # Calculate the joint probability for this specific scenario
                p = joint_probability(people, one_gene, two_genes, have_trait)

                # Add it to our running totals
                update(probabilities, one_gene, two_genes, have_trait, p)

    # Normalize all probability distributions so they sum up to 1
    normalize(probabilities)

    # Print out the final calculated probabilities neatly
    for person in people:
        print(f"{person}:")
        for field in probabilities[person]:
            print(f"  {field.capitalize()}:")
            for value in probabilities[person][field]:
                p = probabilities[person][field][value]
                print(f"    {value}: {p:.4f}")


def load_data(filename):
    """
    Load gene and trait data from a CSV file into a dictionary.
    """
    data = dict()
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"]
            data[name] = {
                "name": name,
                "mother": row["mother"] or None,
                "father": row["father"] or None,
                "trait": (True if row["trait"] == "1" else
                          False if row["trait"] == "0" else None)
            }
    return data


def powerset(s):
    """
    Return a list of all possible subsets of set s.
    """
    s = list(s)
    return [
        set(s) for s in itertools.chain.from_iterable(
            itertools.combinations(s, r) for r in range(len(s) + 1)
        )
    ]


def joint_probability(people, one_gene, two_genes, have_trait):
    """
    Compute and return the joint probability of a specific family state.
    """
    joint_prob = 1.0

    for person, info in people.items():
        # Figure out how many copies of the gene this person has in this scenario
        if person in two_genes:
            gene_count = 2
        elif person in one_gene:
            gene_count = 1
        else:
            gene_count = 0

        has_trait = person in have_trait
        mother, father = info["mother"], info["father"]

        # Step 1: Calculate gene probability based on whether parents are known
        if mother is None and father is None:
            # No parents in data, use unconditional population probabilities
            gene_prob = PROBS["gene"][gene_count]
        else:
            # Parents exist, calculate transmission probabilities with mutation in mind
            def get_inheritance_prob(parent_name):
                if parent_name in two_genes:
                    return 1.0 - PROBS["mutation"]  # Passes gene unless it mutates away
                elif parent_name in one_gene:
                    return 0.5  # 50% chance to pass the gene
                else:
                    return PROBS["mutation"]  # Doesn't have it, but might mutate into it

            mom_pass_prob = get_inheritance_prob(mother)
            dad_pass_prob = get_inheritance_prob(father)

            # Combine parental passing probabilities depending on child's gene count
            if gene_count == 2:
                gene_prob = mom_pass_prob * dad_pass_prob
            elif gene_count == 1:
                gene_prob = (mom_pass_prob * (1.0 - dad_pass_prob)) + \
                            ((1.0 - mom_pass_prob) * dad_pass_prob)
            else:  # gene_count == 0
                gene_prob = (1.0 - mom_pass_prob) * (1.0 - dad_pass_prob)

        # Step 2: Get the probability of expressing the trait given the gene count
        trait_prob = PROBS["trait"][gene_count][has_trait]

        # Multiply into the overall joint probability chain
        joint_prob *= (gene_prob * trait_prob)

    return joint_prob


def update(probabilities, one_gene, two_genes, have_trait, p):
    """
    Add the newly computed joint probability 'p' to each person's distribution.
    """
    for person in probabilities:
        # Determine current person's gene count
        gene_count = (
            2 if person in two_genes
            else 1 if person in one_gene
            else 0
        )
        probabilities[person]["gene"][gene_count] += p

        # Determine current person's trait status
        has_trait = person in have_trait
        probabilities[person]["trait"][has_trait] += p


def normalize(probabilities):
    """
    Normalize each person's probability distributions so they sum to 1.
    """
    for person, fields in probabilities.items():
        for field, distribution in fields.items():
            total_sum = sum(distribution.values())
            if total_sum > 0:
                for value in distribution:
                    distribution[value] /= total_sum


if __name__ == "__main__":
    main()