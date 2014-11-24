#!/usr/bin/env python3

import sys
import praw
import collections
import networkx as nx

DEBUG = True
VERBOSE = True

def print_graph_summary(graph):
    for node in graph.nodes():
        print("node " + node + " has " + str(len(graph.neighbors(node))) + " neighbors")
        print("they are:")
        for neighbor in graph.neighbors(node):
            print(neighbor + "\t" + graph.node[neighbor]['seen'])

def get_top_N_from_month(subreddit, N, r):
    return r.get_subreddit(subreddit).get_top_from_month(limit=N)

def update_graph_with_comment(graph, submission, comment, already_added, r):
    if  isinstance(comment, praw.objects.MoreComments):
        return graph
    if comment.author == None:
        return graph

    this_author = comment.author.name

    # create a node for this_author if necessary
    if this_author not in graph.nodes():
        graph.add_node(this_author, seen=submission.permalink)
        if VERBOSE:
            print("added new author: " + this_author + " (seen: " + graph.node[this_author]['seen'])
    else:
        if VERBOSE:
            print("author already in the graph: " + this_author + " (seen: " + graph.node[this_author]['seen'])
            print("and submission.permalink is " + submission.permalink)
        already_seen = graph.node[this_author]['seen']
        if submission.permalink not in already_seen:
            seen_list = already_seen.split(',')
            seen_list.append(submission.permalink)
            seen_list = sorted(seen_list)
            graph.node[this_author]['seen'] = ','.join(seen_list)
        seen_string = submission.permalink
    # connect this node to all others in the graph from this submission
    for author in already_added:
        graph.add_edge(author, this_author) 

    already_added.append(this_author)

def update_graph_with_submission(graph, submission, r):
    if VERBOSE:
        print("Working on this submission: " + submission.permalink)
        print("  author is " + str(submission.author))

    # TODO deal with MoreComments
    #print("Fetching MoreComments")
    #X = 5 # TODO limit=None
    #submission.replace_more_comments(limit=X, threshold=0)
    #print("Now it has " + str(len(submission.comments)) + " comments")

    flat_comments = praw.helpers.flatten_tree(submission.comments)

    if DEBUG: # fewer comments, faster runtime, smaller graph
        flat_comments = flat_comments[:40]

    if VERBOSE:
        print("It has " + str(len(flat_comments)) + " comments")

    if submission.author == None:
        return graph

    graph.add_node(submission.author.name, seen=submission.permalink) 
    # TODO think long and hard about what to store
    
    already_added = [submission.author.name]
    for comment in flat_comments:
        update_graph_with_comment(graph, submission, comment, already_added, r)
    return graph

def update_graph_with_top_N_submissions_from_month(graph, N, sub, r):
    """Gets top N submissions from given subreddit, updates graph by 'seen in'

    Arguments:
        graph: a NetworkX Graph object
        N: an integer for how many top submissions from month to fetch
        sub: a string representingi the subreddit name
        r: a praw.Reddit object

    Returns:
        the updated Graph object
    """
    top_submissions = get_top_N_from_month(sub, N, r)

    if VERBOSE:
        print("Got " + str(N) + " submission(s) from " + sub)
    
    # loop through submissions, adding each submitter and each commenter to the graph
    for submission in top_submissions:
        graph = update_graph_with_submission(graph, submission, r)
    return graph

def main():
    if len(sys.argv) != 2:
        sys.stderr.write("usage: build_graph_for_one_subreddit.py <subreddit>\n")
        sys.exit()

    sub= sys.argv[1]

    user_agent = ("reddit_sna scraper v0.1 by /u/sna_bot "
                  "https://github.com/brianreallymany/reddit_sna")
    r = praw.Reddit(user_agent=user_agent)

    graph = nx.Graph()

    # get N top submissions from chosen subreddit
    N = 2 # TODO command line arg

    graph = update_graph_with_top_N_submissions_from_month(graph, N, sub, r)

    # Summarize graph
    if VERBOSE:
        print_graph_summary(graph)
        print("writing gexf...")

    nx.write_gexf(graph, 'foo.gexf')

    if VERBOSE:
        print("wrote gexf...")

############################################################################

if __name__ == '__main__':
    main()

