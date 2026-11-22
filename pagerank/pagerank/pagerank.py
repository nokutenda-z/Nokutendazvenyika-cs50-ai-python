import os
import random
import re
import sys

DAMPING = 0.85
SAMPLES = 10000

def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python pagerank.py corpus")
    corpus = crawl(sys.argv[1])
    ranks = sample_pagerank(corpus, DAMPING, SAMPLES)
    print(f"PageRank Results from Sampling (n = {SAMPLES})")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")
    ranks = iterate_pagerank(corpus, DAMPING)
    print(f"PageRank Results from Iteration")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")

def crawl(directory):
    pages = dict()
    for filename in os.listdir(directory):
        if not filename.endswith(".html"):
            continue
        with open(os.path.join(directory, filename)) as f:
            contents = f.read()
            links = re.findall(r"<a\s+(?:[^>]*?)href=\"([^\"]*)\"", contents)
            pages[filename] = set(links) - {filename}
    for filename in pages:
        pages[filename] = set(
            link for link in pages[filename]
            if link in pages
        )
    return pages

def transition_model(corpus, page, damping_factor):
    """
    Return a probability distribution over which page to visit next,
    given a current page.
    """
    distribution = {}
    N = len(corpus)

    # If page has no outgoing links, treat as linking to all pages
    if len(corpus[page]) == 0:
        for p in corpus:
            distribution[p] = 1 / N
        return distribution

    # Base: (1-d)/N for every page
    for p in corpus:
        distribution[p] = (1 - damping_factor) / N

    # Add d / num_links for each linked page
    for linked in corpus[page]:
        distribution[linked] += damping_factor / len(corpus[page])

    return distribution

def sample_pagerank(corpus, damping_factor, n):
    """
    Return PageRank values by sampling n pages.
    """
    counts = {page: 0 for page in corpus}
    # First sample: choose at random
    current = random.choice(list(corpus.keys()))

    for _ in range(n):
        counts[current] += 1
        model = transition_model(corpus, current, damping_factor)
        current = random.choices(
            list(model.keys()),
            weights=list(model.values()),
            k=1
        )[0]

    return {page: count / n for page, count in counts.items()}

def iterate_pagerank(corpus, damping_factor):
    """
    Return PageRank values by iteratively updating until convergence.
    """
    N = len(corpus)
    pagerank = {page: 1 / N for page in corpus}

    while True:
        new_rank = {}
        for page in corpus:
            total = (1 - damping_factor) / N

            for possible_page, links in corpus.items():
                if len(links) == 0:
                    total += damping_factor * pagerank[possible_page] / N
                elif page in links:
                    total += damping_factor * pagerank[possible_page] / len(links)

            new_rank[page] = total

        # Stop when change < 0.001
        if all(abs(new_rank[p] - pagerank[p]) <= 0.001 for p in corpus):
            break

        pagerank = new_rank

    return pagerank

if __name__ == "__main__":
    main()