# Schedule all papers for build

from procbuild import papers, paper_queue

for (nr, info) in papers:
    paper_queue.put(int(nr))
