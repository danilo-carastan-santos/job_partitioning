import os
import subprocess
import json
import yaml
import sys
import random

def preparing_experiments(platforms_path, workloads_path, experiments_description_path, output_dir, output_dir_path, type_of_job, length_of_partition):
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
                
                results_path = output_dir + type_of_job + "/" + length_of_partition + "/" + workload_name + "/"
                cmd = "mkdir " + results_path
                experiments_results_path = output_dir_path + type_of_job + "/" + length_of_partition + "/" + workload_name + "/"
                os.system(cmd)
                
                for workload in list_of_workloads:
                    robin_file = {
                        "batcmd": "batsim " \
                            "-p " + platforms_path + "/" + platform + " " \
                            "-w " + workloads_path + "/" + workload + " " \
                            "-e " + results_path + "out" + "_" + workload.split(".")[0] + " " \
                            "--forward-profiles-on-submission " \
                            "--enable-dynamic-jobs " \
                            "--enable-profile-reuse ",
                        "failure-timeout": "10",
                        "output-dir": results_path,
                        "ready-timeout": "10",
                        "schedcmd": "batsched -v easy_bf_fast",
                        "simulation-timeout": "604800",
                        "success-timeout": "3600"
                    }
                    #print(robin_file)
                    with open(experiment_description_full_path + '/exp_' + workload.split('.json')[0] + '.yaml', 'w') as file:
                        yaml.dump(robin_file, file)

def select_experiments_randomly(list_of_experiments, number_of_experiments_to_run):
    random_positions = random.sample(range(0, len(list_of_experiments)), number_of_experiments_to_run)
    list_of_experiments_filtered = []
    for position in random_positions:
        list_of_experiments_filtered.append(list_of_experiments[position])
    return list_of_experiments_filtered

def running_experiments(workloads_path, experiments_description_path, type_of_job, length_of_partition, nix_env_path, number_of_experiments_to_run):      
    
    # TODO To loop the type_of_job here, Turn it in types_of_job
    
    cmd = "ls " + workloads_path
    workloads_name = subprocess.getoutput(cmd).split("\n")
    print("Names of workloads: ", workloads_name)
    
    # Loop in the robin files and execute it
    for workload in workloads_name:
        experiment_description_path = experiments_description_path + "/" + type_of_job + "/" + length_of_partition + "/" + workload
        cmd = "ls " + experiment_description_path
        list_of_experiments = subprocess.getoutput(cmd).split("\n")

        list_of_experiments_filtered = select_experiments_randomly(list_of_experiments, number_of_experiments_to_run)

        for experiment in list_of_experiments_filtered:
            cmd = "nix-shell " + nix_env_path + " --command 'robin " + experiment_description_path + "/" + experiment + "'"
            print(cmd)
            #os.system(cmd)

def print_parameters():
    str = "\nPlease, use one of the following parameters: \n\
    -h                 | help \n\
    -g | Generate the expe_.yaml files\n\
    -r <num_of_workloads> | Sort the num_of_workloads specified by workload and run them.\n"

    print(str)
    return

def main():
    
    print ('Number of arguments:', len(sys.argv), 'arguments.')
    print ('Argument List:', str(sys.argv))

    platforms_path = "../platforms"
    length_of_partition = "two_weeks"
    experiments_description_path = "./description"
    nix_env_path = "./nix-env.nix"
    output_dir = "./results/"
    output_dir_path = "../../../../results/" # Path from inside the expe.yaml files
    type_of_jobs = ["original", "partitioned"]

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
                preparing_experiments(
                    platforms_path, 
                    workloads_path, 
                    experiments_description_path,
                    output_dir,
                    output_dir_path,
                    type_of_job,
                    length_of_partition
                )
        elif(argvs[1] == "-r"):
            if (len(argvs) == 3):
                for type_of_job in type_of_jobs:
                    workloads_path = "../workloads/json/" + type_of_job + "/two_weeks"
                    running_experiments(
                        workloads_path, 
                        experiments_description_path, 
                        type_of_job, 
                        length_of_partition, 
                        nix_env_path,
                        int(argvs[2]))

        else:
           print_parameters()

main()

