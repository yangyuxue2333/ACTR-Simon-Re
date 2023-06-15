import os
import pandas as pd
import actr
import numpy as np
import math
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import date
import natsort
import itertools

class MiniModel:
    def __init__(self, num_productions=10, param_set=None):
        self.curr_index = 0
        self.curr_onset = 0
        self.curr_offset = 0
        self.curr_production = ""
        self.ordered_productions = ["P"+str(i+1) for i in range(num_productions)]
        self.production_at = np.arange(1, num_productions+1)/100
        self.production_reward = range(num_productions)
        
        self.trial_trace = []
        self.production_trace = []
        self.reward_trace = []
        self.utility_trace = []
        
        self.param_set = param_set
    
    def setup_model(self, model="mini-model.lisp", retrieve=False):
        curr_dir = os.path.dirname(os.path.realpath('__file__'))
        actr.load_act_r_model(os.path.join(curr_dir, model))
        if retrieve:
            actr.pdisable('skip-retrieval')
        else:
            actr.pdisable('retrieve-rule')
        self.setup_parameters()
    
    def cost_function(self, x, a=50, enable=True):
        c = np.exp(x*a)/a
        if enable:
            return np.round(c, 4)
        else:
            return x

    def payoff_function(self, x, l=10, k=1, x0=5, enable=True):
        """
        sigmoid function
            x0 = mid point
            l = max 
            k = slope
        """
        r = l / (1 + np.exp(-k * ( x - x0)))
        if enable:
            return np.round(r, 4)
        else: 
            return x
        
    def setup_parameters(self):
        actr.hide_output()
        # set at parameter
        
        # set difficulty level
        x0 = 5
        l = 10
        if self.param_set and 'difficulty' in self.param_set.keys():
            x0 = self.param_set['difficulty']
        if self.param_set and 'payoff' in self.param_set.keys():
            l = self.param_set['payoff']

        self.production_at = [self.cost_function(x) for x in self.production_at]
        #self.production_reward = [self.payoff_function(x, x0=x0, l=l) for x in self.production_reward]
        self.production_reward = [self.payoff_function(x, x0=l/2, l=l) for x in self.production_reward]
        
        for i in range(len(self.ordered_productions)):
            actr.spp(self.ordered_productions[i], ":at", self.production_at[i], ":reward", self.production_reward[i])
        #actr.spp("DONE", ":reward", 1)
        actr.unhide_output() 
        

    def production_hook(self, *params):
        #print('in p hook', params)
        production = params[0]
        if production == "START-TRIAL":
            self.curr_index += 1
            self.curr_onset = actr.mp_time()
        elif production == "DONE":
            self.curr_offset = actr.mp_time()
            self.trial_trace.append((self.curr_index, self.curr_production, np.round(self.curr_offset-self.curr_onset, 2)))
            #print(self.curr_index, self.curr_onset, self.curr_offset, self.curr_offset-self.curr_onset)
        elif production in self.ordered_productions:
            self.production_trace.append((self.curr_index, production, actr.mp_time()))
            self.curr_production = production
        return production
    
    def reward_hook(self, *params):
        production = params[0]
        delivered_reward = params[1]
        discounted_reward = params[2]
        if production in self.ordered_productions:
            #print('in reward hook', production)
            self.reward_trace.append((self.curr_index, production, actr.mp_time(), delivered_reward, discounted_reward))
        return (params)

    def utility_hook(self, *params):
        #print('u', len(params), params)
        # NEW: record the production utility
        #self.current_trial.utility_trace=[self.extract_production_parameter('PROCESS-SHAPE', ':u'),
        #                                     self.extract_production_parameter('PROCESS-LOCATION', ':u'),
        #                                     self.extract_production_parameter('DONT-PROCESS-SHAPE', ':u'),
        #                                     self.extract_production_parameter('DONT-PROCESS-LOCATION', ':u')]
        #print(self.extract_production_parameter('P1', ':u'))
        pass
          
    def extract_production_parameter(self, epoch):
        """
        This function will extract the parameter value of a production during model running
        """
        #assert (production_name in actr.all_productions() and
        #        parameter_name in [':u', ':utility', ':at', ':reward', ':fixed-utility'])
        utility_trace = []
        actr.hide_output()
        for production_name in self.ordered_productions:
            u = actr.spp(production_name, ":u")[0][0]
            utility = actr.spp(production_name, ":utility")[0][0]
            reward = actr.spp(production_name, ":reward")[0][0]
            utility_trace.append((epoch, production_name, u, utility, reward))
        actr.unhide_output()
        return pd.DataFrame(utility_trace, columns=['epoch','production', 'u', 'utility', 'delivered_reward'])
    
    def df_trace_output(self):
        df_trial_trace = pd.DataFrame(self.trial_trace, columns=['trial', 'production', 'response_time'])
        df_production_trace = pd.DataFrame(self.production_trace, columns=['trial', 'production', 'firing_time'])
        df_reward_trace = pd.DataFrame(self.reward_trace, columns=['trial', 'production', 'rewarded_time', 'delivered_reward', 'passed_time'])
        df_reward_trace['received_reward'] = df_reward_trace['delivered_reward']-df_reward_trace['passed_time']
        df_cost = pd.DataFrame(list(zip(self.ordered_productions, self.production_at)), columns=["production", "at"])
        df_utility_trace = pd.merge(self.utility_trace, df_cost)
        df = pd.merge(pd.merge(pd.merge(df_trial_trace, 
                                        df_production_trace, on=['trial', 'production']),
                               df_reward_trace, on=['trial', 'production']), 
                      df_utility_trace, on=["production", "delivered_reward"]).drop_duplicates()
        df["difficulty"] = self.param_set["difficulty"]
        df["payoff"] = self.param_set["payoff"]
        return df
        #return (df_trial_trace, df_production_trace, df_reward_trace, df_utility_trace)
        
    def experiment(self, time=100):
        actr.add_command("production-hook",self.production_hook)
        actr.add_command("reward-hook", self.reward_hook)
        actr.add_command("utility-hook", self.utility_hook)
        actr.schedule_event_relative(0.01, "production-hook")
        actr.schedule_event_relative(0.01, "reward-hook")
        actr.schedule_event_relative(0.01, "utility-hook")

        self.setup_model()
        actr.run(time)
        actr.remove_command("production-hook")
        actr.remove_command("reward-hook")
        actr.remove_command("utility-hook")

def simulation(epoch=1, time=100, param_set=None):
    simulated_results = []
    for i in range(epoch):
        if i%(epoch/10) == 0: 
            print("==== SIMULATED ==== epoch >>", i)
            print("PARAMETERS: ", param_set)
        m = MiniModel(param_set=param_set)
        m.experiment(time=time)
        
        # record utility
        m.utility_trace = m.extract_production_parameter(i)
        simulated_results.append(m)
    return simulated_results


def merge_simulation_data(results):
    n = len(results)
    dfs = [results[i].df_trace_output() for i in range(n)]
    df = pd.concat(dfs, axis=0)
    
    # shift column 'epoch' to first position
    first_column = df.pop('epoch')
    df.insert(0, 'epoch', first_column)
    df.sort_values(['epoch', 'trial'], inplace=True)
    
    return df

def run_simulation():
    difficulty = [3,5,7]
    payoff = [10, 15, 20]
    params = list(itertools.product(*[difficulty, payoff]))

    dfs = []
    for p in params:
        rs = simulation(epoch=100, time=100, param_set={'difficulty':p[0], 'payoff':p[1]})
        df = merge_simulation_data(rs)
        dfs.append(df)
    df = pd.concat(dfs)
    return df



