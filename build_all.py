# Schedule all papers for build

from procbuild import papers, paper_queue

for (nr, info) in papers:
    print "Placing %s in the build queue." % nr
    paper_queue.put(int(nr))

# Add sentinel to queue
paper_queue.put(None)
