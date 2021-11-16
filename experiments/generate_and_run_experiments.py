import os
import subprocess
import json
import yaml
import sys
import random
import time

def preparing_experiments(
    platforms_path,
    workloads_path,
    experiments_description_path,
    output_dir,
    type_of_job,
    length_of_partition):
    """
    Prepare a robin file description for each experiment, by platform, workload and type_of_job, and save them in yaml files
    in the experiments_description_path.
    """
    
    cmd = 'ls ' + platforms_path
    list_of_platforms = subprocess.getoutput(cmd).split("\n")
    print("List of platforms: ", list_of_platforms)
    
    cmd = "ls " + workloads_path
    workloads_name = subprocess.getoutput(cmd).split("\n")
    print("Names of workloads: ", workloads_name)

    for platform in list_of_platforms:
        for workload_name in workloads_name:
            if(platform.split(".xml")[0] == workload_name):
                cmd = "ls " + workloads_path + "/" + workload_name + "/"
                list_of_workloads = subprocess.getoutput(cmd).split("\n")
                
                experiment_description_full_path = experiments_description_path + "/" + type_of_job + "/" + length_of_partition + '/' + workload_name
                cmd = "mkdir " + experiment_description_full_path
                os.system(cmd)
                
                results_path = output_dir + "/" + type_of_job + "/" + length_of_partition + "/" + workload_name #+ "/"
                cmd = "mkdir " + results_path
                os.system(cmd)
                
                for workload in list_of_workloads:
                    output_path = results_path + "/" + workload
                    cmd = "mkdir " + results_path
                    os.system(cmd)
                    robin_file = {
                        "batcmd": "batsim " \
                            "-p " + platforms_path + "/" + platform + " " \
                            "-w " + workloads_path + "/" + workload_name + "/" + workload + " " \
                            "-e " + output_path + "/out_" + workload.split(".")[0] + " ",
                        "failure-timeout": 10,
                        "output-dir": output_path,
                        "ready-timeout": 10,
                        "schedcmd": "batsched -v easy_bf_fast",
                        "simulation-timeout": 604800,
                        "success-timeout": 3600
                    }
                    #print(robin_file)
                    with open(experiment_description_full_path + '/exp_' + workload.split('.json')[0] + '.yaml', 'w') as file:
                        yaml.dump(robin_file, file)

def select_experiments_randomly(list_of_experiments, number_of_experiments_to_run):
    """
    Receive a number_of_experiments_to_run and a list_of_experiments.
    Generate n random numbers (number_of_experiments_to_run) and select experiments from list_of_experiments in such positions.
    Return such selected list. 
    Notice that we receive a seed, to use the same random number for both types of experiments, original and partitioned.
    """

    random_positions = random.sample(range(0, len(list_of_experiments)), number_of_experiments_to_run)
    list_of_experiments_filtered = []
    for position in random_positions:
        list_of_experiments_filtered.append(list_of_experiments[position])
    return list_of_experiments_filtered

def list_experiments(workloads_path, experiments_description_path, type_of_job, length_of_partition, nix_env_path, number_of_experiments_to_run, random_seed):
    """
    Check all experiment files and list them together. Return such list.
    """
    
    # Use a random seed to get the same results for both original and partitioned jobs
    random.seed(random_seed) 

    cmd = "ls " + workloads_path
    workloads_name = subprocess.getoutput(cmd).split("\n")
    workloads_name.remove("trinity_formatted_release_v0.1.0")
    
    # Loop in the robin files and add them in the list_of_executions
    list_of_executions = []
    for workload in workloads_name:
        experiment_description_path = experiments_description_path + "/" + type_of_job + "/" + length_of_partition + "/" + workload
        cmd = "ls " + experiment_description_path
        list_of_experiments = subprocess.getoutput(cmd).split("\n")

        list_of_experiments_filtered = select_experiments_randomly(list_of_experiments, number_of_experiments_to_run)

        for experiment in list_of_experiments_filtered:
            cmd = "nix-shell " + nix_env_path + " --command 'robin " + experiment_description_path + "/" + experiment + "'"
            list_of_executions.append(cmd)

    return list_of_executions, workloads_name

def sort_experiments_by_workload(list_of_experiments, list_of_workloads):
    """
    Sort the list_of_experiments by a sorted list_of_workloads. 
    This method help us to organize the order of execution of the experiments. 
    This way we can run all experiments from both types original and parititioned by workload.
    """

    list_of_experiments_sorted = []
    for workload in sorted(list_of_workloads):
        for experiment in list_of_experiments:
            if (workload in experiment):
                list_of_experiments_sorted.append(experiment)
    return list_of_experiments_sorted

def run_experiments(list_of_experiments):
    """
    Run all experiment in list_of_experiments.
    """
    global_start_time = time.time()
    for experiment in list_of_experiments:
        local_start_time = time.time()
        print("---------------------------------------------------------\n") 
        print("Executing the following: \n" + experiment + "\n")
        #os.system(experiment)
        local_finish_time = time.time()
        print("-- Simulation finished, duration: " + str(local_finish_time - local_start_time)  + " seconds\n")
    global_finish_time = time.time()
    print("---------------------------------------------------------")
    print("---------------------------------------------------------\n")
    print("All simulations were finished, global duration: " + str(global_finish_time - global_start_time) + " seconds\n")
    return      

def print_parameters():
    str = "\nPlease, use one of the following parameters: \n\
    -h | Help \n\
    -g | Generate the expe_.yaml files\n\
    -r <num_of_workloads> | Sort the num_of_workloads specified by workload and run them.\n"

    print(str)
    return

def main():
    
    # Define parameters
    length_of_partition = "two_weeks"
    
    platforms_path = "../platforms"
    experiments_description_path = "./description"
    nix_env_path = "./nix-env.nix"
    output_dir = "./results"
    
    # Path from inside the expe.yaml files
    #platforms_dir_path = "../../../../../platforms"
    #output_dir_path = "../../../../results" 
    
    type_of_jobs = ["original", "partitioned"]
    random_seed = random.random()

    # List of command lines to execute each experiment
    list_of_executions_combined = []

    # Check and execute the methods by parameters
    argvs = sys.argv

    if (len(argvs) == 1):
        print_parameters()
        return

    else:
        if(argvs[1] == "-g"):
            for type_of_job in type_of_jobs:
                os.system("mkdir ./description/" + type_of_job)
                os.system("mkdir ./description/" + type_of_job + "/" + length_of_partition)

                os.system("mkdir ./results/" + type_of_job)
                os.system("mkdir ./results/" + type_of_job + "/" + length_of_partition)

                workloads_path = "../workloads/json/" + type_of_job + "/two_weeks"
                #workloads_dir_path = "../../../../../workloads/json/" + type_of_job + "/two_weeks"

                preparing_experiments(
                    platforms_path,
                    #platforms_dir_path,
                    workloads_path,
                    #workloads_dir_path,
                    experiments_description_path,
                    output_dir,
                    #output_dir_path,
                    type_of_job,
                    length_of_partition
                )

        elif(argvs[1] == "-r"):
            if (len(argvs) == 3):
                for type_of_job in type_of_jobs:

                    # Get the list of experiments
                    workloads_path = "../workloads/json/" + type_of_job + "/two_weeks"
                    list_of_executions, list_of_workloads = list_experiments(
                        workloads_path, 
                        experiments_description_path, 
                        type_of_job, 
                        length_of_partition, 
                        nix_env_path,
                        int(argvs[2]),
                        random_seed)
                    list_of_executions_combined += list_of_executions

                # Sort the list of exeuctions by workload. 
                # Then we will run original and partitioned in sequence (for each workload).
                list_of_executions_combined = sort_experiments_by_workload(list_of_executions_combined, list_of_workloads)
                
                # Run the experiments
                run_experiments(list_of_executions_combined)

        else:
           print_parameters()

main()

