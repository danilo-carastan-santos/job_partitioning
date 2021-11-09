import pandas as pd
import numpy as np
import os
import argparse
import re
import subprocess

SEC_ONE_MINUTE=60
SEC_ONE_HOUR=3600.0
SEC_ONE_DAY=SEC_ONE_HOUR*24
SEC_ONE_WEEK=SEC_ONE_DAY*7
SEC_TWO_WEEKS=SEC_ONE_WEEK*2
SEC_TWO_DAYS=SEC_ONE_DAY*2

JSON_COMP_SPEED='1e6'

SWF_FIELDS=['JOB_ID',
                'SUBMIT_TIME',
                'WAIT_TIME',
                'RUN_TIME',
                'ALLOCATED_PROCESSOR_COUNT',
                'AVERAGE_CPU_TIME_USED',
                'USED_MEMORY',
                'REQUESTED_NUMBER_OF_PROCESSORS',
                'REQUESTED_TIME',
                'REQUESTED_MEMORY',
                'STATUS',
                'USER_ID',
                'GROUP_ID',
                'APPLICATION_ID',
                'QUEUD_ID',
                'PARTITION_ID',
                'PRECEDING_JOB_ID',
                'THINK_TIME_FROM_PRECEDING_JOB']

def init():
    class WorkloadProps:
        def __init__ (self, max_walltime, max_procs):
            self.max_walltime=max_walltime
            self.max_procs=max_procs

    ## max_walltime and max_procs extracted from workload "FAQ" (for mustand and trinity)
    ## and from the parallel workloads archive for the rest
    dct_workload_props = {
        'trinity_formatted_release_v0.1.0': WorkloadProps(max_walltime=36*SEC_ONE_HOUR, max_procs=301056),
        'mustang_release_v0.2.0': WorkloadProps(max_walltime=16*SEC_ONE_HOUR, max_procs=38400),
        'HPC2N-2002-2.2-cln': WorkloadProps(max_walltime=432000.0, max_procs=240),
        'SDSC-BLUE-2000-4.2-cln':  WorkloadProps(max_walltime=129600.0, max_procs=1152)
       }
    return dct_workload_props

##perform a small sanity check on the job walltimes and compute new job ids
def parse_job(job, lst_workload_newids):
    ##dirty hack to deal with jobs that finish on the walltime
    ##AND just few seconds longer than the walltime
    if job['RUN_TIME'] >= job['REQUESTED_TIME']:
        job['RUN_TIME']=job['REQUESTED_TIME']
    lst_workload_newids.append('job_'+str(int(job['JOB_ID'])))
    return job

def read_input_swf(swf_filename, dct_workload_props):
    regex = '(.*)_\d+.swf'    
    basename=os.path.basename(swf_filename)
    #print(basename)
    res = re.search(regex, basename)
    trace_name = res.group(1)    
    ##setting the max walltime and the partitioning threshold according to the
    ##workload
    SEC_WALLTIME_LIMIT=dct_workload_props[trace_name].max_walltime
    SEC_HALF_WALLTIME_LIMIT=SEC_WALLTIME_LIMIT/2

    df_workload=pd.read_csv(swf_filename, sep=' ', names=SWF_FIELDS)

    lst_workload_newids=[]

    df_workload=df_workload.apply(lambda job: parse_job(job, lst_workload_newids), axis=1)

    ## assign the new job ids
    df_workload.loc[:,'JOB_ID']=lst_workload_newids

    swf_outfile_name='../workloads/swf/original/original_renamed_jobs/two_weeks/'+trace_name+'/'+basename
    ##save the original workload with the job ids renamed
    df_workload.to_csv(swf_outfile_name, sep=' ', header=False, index=False)

    #call swftojson and save the json file
    json_outfile_name='../workloads/json/original/two_weeks/'+trace_name+'/'+re.sub('.swf', '', basename)+'.json'
    lst_call_command=['python',
                      'swf_to_batsim_workload_compute_only.py',
                      '-q',
                      '-cs', JSON_COMP_SPEED,
                      '-pf',
                      str(dct_workload_props[trace_name].max_procs),
                      swf_outfile_name,
                      json_outfile_name]
    #print(lst_call_command)
    subprocess.call(lst_call_command)

    ##long jobs = jobs that will be partitioned
    ##short jobs = jobs that will be unchanged
    df_long_jobs=df_workload.loc[df_workload['REQUESTED_TIME'] >= SEC_HALF_WALLTIME_LIMIT]
    df_short_jobs=df_workload.loc[df_workload['REQUESTED_TIME'] < SEC_HALF_WALLTIME_LIMIT]
    
    return df_long_jobs, df_short_jobs, trace_name, basename

def partition_job(job, lst_partitioned_jobs):
    ##dirty hack to deal with jobs that finish on the walltime
    ##AND just few seconds longer than the walltime
    ##this is done on the original workload, it's here for safety
    if job['RUN_TIME'] >= job['REQUESTED_TIME']:
        job['RUN_TIME']=job['REQUESTED_TIME']
    
    nb_partitions=int(np.ceil(job['RUN_TIME']/SEC_ONE_HOUR))
    subm_time=job['SUBMIT_TIME']
    #job_id_prefix=str(int(job['JOB_ID']))
    for i in range(nb_partitions):
        partition=job.copy()
        partition['SUBMIT_TIME']=subm_time
        subm_time=subm_time+SEC_ONE_HOUR
        if i == (nb_partitions-1) and (job['RUN_TIME']%SEC_ONE_HOUR) > 0:
            run_time=job['RUN_TIME']%SEC_ONE_HOUR
        else:
            run_time=SEC_ONE_HOUR
        partition['RUN_TIME']=run_time
        partition['REQUESTED_TIME']=SEC_ONE_HOUR
        #partition['JOB_ID']='job_'+job_id_prefix+'_'+str(i)
        partition['JOB_ID']=partition['JOB_ID']+'_'+str(i)
        lst_partitioned_jobs.append(partition)


def partition_workload(df_long_jobs, df_short_jobs, trace_name, base_name, dct_workload_props):
    lst_partitioned_jobs=[]

    df_long_jobs.apply(lambda job: partition_job(job, lst_partitioned_jobs), axis=1)

    #print(lst_partitioned_jobs)   
    df_partitioned_jobs=pd.DataFrame(lst_partitioned_jobs)


    ##dataframe for the short jobs with renamed ids. i add a suffix _0 for them
    df_renamed_short_jobs=df_short_jobs.copy()

    lst_new_job_ids=[]

    for index, job in df_short_jobs.iterrows():
        #lst_new_job_ids.append('job_'+str(int(job['JOB_ID']))+'_0')
        lst_new_job_ids.append(job['JOB_ID']+'_0')

    df_renamed_short_jobs.loc[:,'JOB_ID']=lst_new_job_ids

    ##concatenating the unchanged jobs with the partitioned ones
    df_partitioned_workload=pd.concat([df_renamed_short_jobs, df_partitioned_jobs])
    df_partitioned_workload=df_partitioned_workload.sort_values(by='SUBMIT_TIME').reset_index(drop=True)

    swf_outfile_name='../workloads/swf/partitioned/two_weeks/'+trace_name+'/'+base_name
    df_partitioned_workload.to_csv(swf_outfile_name, 
                                   sep=' ', header=False, index=False)

    #call swftojson and save the json file
    json_outfile_name='../workloads/json/partitioned/two_weeks/'+trace_name+'/'+re.sub('.swf', '', base_name)+'.json'
    lst_call_command=['python',
                      'swf_to_batsim_workload_compute_only.py',
                      '-q',
                      '-cs', JSON_COMP_SPEED,
                      '-pf',
                      str(dct_workload_props[trace_name].max_procs),
                      swf_outfile_name,
                      json_outfile_name]
    #print(lst_call_command)
    subprocess.call(lst_call_command)
 


def main():
    """
    Program entry point.

    Parses the input arguments then perform the workload partitioning.
    """
    parser = argparse.ArgumentParser(
        description='Reads a folder of SWF files and creates to copies (one SWF and another json) with some jobs partitiones')
    parser.add_argument('--input_swf_path', type=str,
                        help='The input SWF files folder')
   

    args = parser.parse_args()
    swf_input_path=args.input_swf_path
    #swf_input_path='../workloads/test_mustang_release_v0.2.0_66.swf'
    #swf_output_path='../workloads/partitioned/'
    dct_workload_props = init()
    for file_str in os.listdir(swf_input_path):
        if file_str.endswith('.swf'):
            file_path=swf_input_path+'/'+file_str
            df_long_jobs, df_short_jobs, trace_name, base_name = read_input_swf(file_path, dct_workload_props)
            partition_workload(df_long_jobs, df_short_jobs, trace_name, base_name, dct_workload_props)
    
if __name__ == "__main__":
    main()
