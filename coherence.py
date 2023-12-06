"""
THIS FILE IS NOT GRADED.

We define a "runner" class here which is used to test the coherence protocol.
You should use this to test your code and the autograder uses a version of this
runner to grade your assignment too. 

Please make sure that your code runs error free and to completion with this
runner.
"""

import argparse
import json
import os
import sys

from typing import List

from mesi import MESICoherence

_ARG_DESC = """
CS 433 Fall 2023 HW 6 Tester.
 """
_HELP_MSG = """
This tester runs your cache coherence code on a trace. You can find an example traces in the traces/ directory.
For any questions and clarifications, you can reach the course staff by making a post on Campuswire. Enjoy coding!
"""

_TEST_ALGOS = ["mesi"]

def parse_trace_file(trace_file_path : str) -> List[List]:
    trace_list = list()
    with open(trace_file_path) as trace_file:
        for trace in trace_file:
            trace_array = trace.split(",")
            trace_list.append(trace_array)
    return trace_list

def get_loc_list(loc_list, no_state = False):
    ret_list = list()
    for _, loc in loc_list.items():
        if no_state:
            ret_list.append({
                "addr" : loc.addr, 
                "data" : loc.data
                })
        else:
            ret_list.append({
                "addr" : loc.addr, 
                "data" : loc.data, 
                "state" : loc.state.name
                })
    return ret_list

def run_tester(trace_path : str, output_path : str):
    trace_list = parse_trace_file(trace_path)
    json_output = dict()
    cache_state = list()

    if len(trace_list) < 2:
        raise Exception("Trace file too short")

    system_info = trace_list[0]

    if len(system_info) != 3:
        raise Exception("System information in trace invalid")

    cpu_count = int(system_info[0])
    json_output["cpu_count"] = cpu_count

    priv_cache_size = int(system_info[1])
    json_output["private_cache_size"] = priv_cache_size
    
    llc_size = int(system_info[2])
    json_output["llc_size"] = llc_size

    coherence = MESICoherence(cpu_count, priv_cache_size, llc_size)
    
    i = 1
    ld_count = 0
    correct_count = 0

    while i < len(trace_list):
        trace = trace_list[i]
        cpu_id = int(trace[1])
        addr = int(trace[2])
        data = int(trace[3])

        iter_state = dict()
        priv_cache_state = dict()

        iter_state["timestamp"] = i - 1
        iter_state["command"] = trace[0]
        iter_state["addr"] = addr
        iter_state["command_cpu"] = cpu_id

        if trace[0] == "LD":
            data_ret = coherence.load_data(addr, cpu_id)
            ld_count += 1
            if data_ret is None:
                iter_state["data_return"] = "Empty"
            else:
                iter_state["data_return"] = data_ret
            iter_state["data_expected"] = data
            if data_ret == data:
                correct_count += 1
        
        if trace[0] == "ST":
            iter_state["data_added"] = data
            coherence.store_data(data, addr, cpu_id)
        
        for k in range(cpu_count):
            priv_cache_list = get_loc_list(coherence.cpu_cache[k]._data)
            if len(priv_cache_list) != 0:
                priv_cache_state[k] = priv_cache_list
            else:
                priv_cache_state[k] = "Empty"
        iter_state["priv_cache"] = priv_cache_state
        
        llc_list = get_loc_list(coherence.llc._data, True)
        iter_state["llc"] = llc_list

        memory_list = get_loc_list(coherence.main_memory._data, True)
        iter_state["main_memory"] = memory_list

        cache_state.append(iter_state)
        coherence.tick()
        i += 1

    json_output['commands'] = cache_state
    print("{}/{} load commands return expected value".format(correct_count, ld_count))
    if output_path is not None:
        output_file = open(output_path, "w")
        output_file.write(json.dumps(json_output))
        output_file.close()
        print("Output file written to {}".format(output_path))

def main():
    parser = argparse.ArgumentParser(add_help = False, description=_ARG_DESC, epilog = _HELP_MSG)
    parser.add_argument("-h", "--help", action = "help", default=argparse.SUPPRESS, help = "Tester documentation")
    parser.add_argument("-t", "--trace", help = "Path to trace file", metavar="", required=True, nargs=1)
    parser.add_argument("-o", "--output", help = "Output program output", metavar="", required=False, nargs=1)
    args = parser.parse_args()

    trace_path = args.trace[0]

    if not os.path.isfile(trace_path):
        print("Trace file path \"{}\" invalid".format(trace_path))
        sys.exit(1)

    output_path = None

    if args.output is not None:
        output_path = args.output[0]

    run_tester(trace_path, output_path)

if __name__=="__main__":
    main()
