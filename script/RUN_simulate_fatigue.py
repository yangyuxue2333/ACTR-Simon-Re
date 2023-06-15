from simon_device import *
import itertools

def run_simulation_fatigue(model="simon-motivation-model3", param_set=None, n_simulation=100, n_session=1, verbose=True, log=True, special_suffix=""):
    """
    Run simulation for different parameters

    """

    data_dir = os.path.join(os.path.realpath(".."), "data")
    time_suffix = datetime.now().strftime("%Y%m%d%H%M%S") + special_suffix
    dfs_model = []
    dfs_trace = []
    dataframes_params = []

    # number of simulation per parameter sets
    for j in range(n_simulation):
        if verbose: print("Epoch #%03d" % j)

        # number of sessions per experiment
        dffs_model = []
        dffs_trace = []
        for i in range(n_session):
            if verbose: print("\tSession #%03d" % i)
            if i<6:
                pass
            else:
                param_set["motivation"] = 10
            print(i, param_set)
            session = run_experiment(model,
                                     reload=(not i),
                                     visible=False,
                                     verbose=True,
                                     trace=False,
                                     param_set=param_set)
            session_model=session.df_stats_model_outputs()
            session_trace=session.df_stats_trace_outputs()

            # log parameter file
            session_params = pd.Series(session.parameters)
            session_params['file_suffix'] = str(time_suffix)
            session_params['session'] = i+1

            # log session index
            session_model.insert(0, "session", i+1)
            session_trace.insert(0, "session", i+1)

            dffs_model.append(session_model)
            dffs_trace.append(session_trace)
            dataframes_params.append(session_params)
                

        simulation_model = pd.concat(dffs_model, axis=0)
        simulation_trace = pd.concat(dffs_trace, axis=0)

        # log simulation index
        simulation_model.insert(0, "epoch", j+1)
        simulation_trace.insert(0, "epoch", j+1)

        # append all sessions
        dfs_model.append(simulation_model)
        dfs_trace.append(simulation_trace)


    df_model = pd.concat(dfs_model, axis=0)
    df_trace = pd.concat(dfs_trace, axis=0)
    df_param = pd.DataFrame(dataframes_params)
    if log:
        if log=="summary_stat":
            print("......>>> SAVING SUMMARY STATS <<<......")
            pass
            #TODO: reduce simulation work. Now we set seeds so n=1 will be enough
        else:
            print("......>>> SAVING SIMULATION DATA <<<......")
            df_model["file_suffix"] = str(time_suffix)
            df_trace["file_suffix"] = str(time_suffix)
            df_model.to_csv(os.path.join(data_dir, "model_output_{}.csv".format(time_suffix)), index=False)
            df_trace.to_csv(os.path.join(data_dir, "trace_output_{}.csv".format(time_suffix)), index=False)

            no_parameter_log = not os.path.exists(os.path.join(data_dir, "log.csv"))
            df_param.to_csv(os.path.join(data_dir, "log.csv"), mode='a', index=False, header=no_parameter_log)
    return df_model, df_trace, df_param