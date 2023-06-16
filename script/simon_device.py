## ================================================================ ##
## SIMON.PY                                                        ##
## ================================================================ ##
## A simple ACT-R device for the SIMON task                        ##
## -----------------------------------------                        ##
## This is a device that showcases the unique capacities of the new ##
## JSON-RPC-based ACT-R interface. The device is written in Python, ##
## and interacts with ACT-R entirely through Python code.           ##
## The Simon task is modeled after Andrea Stocco's (2016)          ##
## paper on the Simon task.                           ##
## ================================================================ ##

import os
import actr
import random
import numpy as np
import pandas as pd
import json
import time
from datetime import datetime
from functools import reduce
import scipy.optimize as opt
from tqdm.auto import tqdm

SHAPES = ("CIRCLE", "SQUARE")
LOCATIONS = ("LEFT", "RIGHT")
CONDITIONS = ("CONGRUENT", "INCONGRUENT")

SIMON_MAPPINGS = {"CIRCLE": "LEFT", "SQUARE": "RIGHT"}
RESPONSE_MAPPINGS = {"LEFT": "f", "RIGHT": "j"}
CUE_CONDITIONS = ("CONGRUENT-VALID", "CONGRUENT-INVALID", "INCONGRUENT-VALID", "INCONGRUENT-INVALID")

SEED = 100


class SimonStimulus:
    """An abstract Stroop task stimulus"""

    def __init__(self, shape, location, cue):
        assert (shape in SHAPES and location in LOCATIONS and cue in LOCATIONS)
        self.shape = shape
        self.location = location
        self.cue = cue

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, val):
        self._location = val

    @property
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, val):
        self._shape = val

    @property
    def cue(self):
        return self._cue

    @cue.setter
    def cue(self, val):
        self._cue = val

    @property
    def congruent(self):
        if SIMON_MAPPINGS[self.shape] == self.location:
            return True
        else:
            return False

    @property
    def incongruent(self):
        if SIMON_MAPPINGS[self.shape] != self.location:
            return True
        else:
            return False

    @property
    def valid(self):
        if SIMON_MAPPINGS[self.shape] == self.cue:
            return True
        else:
            return False

    @property
    def invalid(self):
        if SIMON_MAPPINGS[self.shape] != self.cue:
            return True
        else:
            return False

    @property
    def kind(self):
        """Returns the trial type (congruent, incongruent)"""
        res = ""
        if self.congruent:
            res = "congruent"
        elif self.incongruent:
            res = "incongruent"
        return res

    @property
    def cue_kind(self):
        """Returns the cue type (valid, invalid)"""
        res = ""
        if self.valid:
            res = "valid"
        elif self.invalid:
            res = "invalid"
        return res

    def __str__(self):
        return "<[%s]'%s' at %s; cue: '%s' is [%s]>" % (self.kind, self.shape, self.location, self.cue, self.cue_kind)

    def __repr__(self):
        return self.__str__()

class SimonTrial:
    """A class for recording a Stroop trial"""

    def __init__(self, stimulus):
        """Inits a stroop trial"""
        self.stimulus = stimulus
        self.setup()

    def setup(self):
        "Sets up properly"
        self.shape = self.stimulus.shape
        self.location = self.stimulus.location
        self.cue = self.stimulus.cue
        self.onset = 0.0
        self.offset = 0.0
        self.response = None

        # record the utility vlaue of each productions during model running
        self.utility_trace = []         # record ':u' values for 4 competitive productions
        self.check_utility_trace = []  # record ':u' values for 2 check productions: CHECK-PASS-M3, DONT-CHECK
        self.cost = 0.0                # record ':at' for any production
        self.chunk_trace = []           # record ':activation' for 2 simon rules

        # record control intensity
        self.check_count = 0             # record number of checks before responding
        self.check_onset = 0.0          # record onset of checking
        self.check_offset = 0.0         # record offset of checking
        self.responded = False          # track whether has reponded or not
        self.detect_problem = False     # track whether has checked and detected problem or not
        self.expected_reward_check = []          # track CHECK, NO-CHECK expected reward


    ################# BEHAVIOR LOG #####################
    @property
    def correct_response(self):
        return RESPONSE_MAPPINGS[SIMON_MAPPINGS[self.shape]]

    @property
    def accuracy(self):
        if self.response is not None and \
                self.response == self.correct_response:
            return 1.0
        else:
            return 0.0

    @property
    def response_time(self):
        return self.offset - self.onset

    ################# ACT-R TRACE LOG #####################
    @property
    def utility_trace(self):
        """
        This property defines the actr parameter traces
        Trace follow the dict format: self.utility_trace = [(production1, paramter1, value1), ...]
        """
        return self._utility_trace

    @utility_trace.setter
    def utility_trace(self, trace):
        self._utility_trace = trace

    @property
    def check_utility_trace(self):
        """
        This property defines the actr parameter traces
        Trace follow the dict format: self.check_utility_trace = [(production1, paramter1, value1), ...]
        """
        return self._check_utility_trace

    @check_utility_trace.setter
    def check_utility_trace(self, trace):
        self._check_utility_trace = trace

    @property
    def cost(self):
        """
        This property defines the actr production :at parameter traces
        Trace follow the dict format: self.cost = 0.05
        """
        return self._cost

    @cost.setter
    def cost(self, value):
        self._cost = value

    @property
    def chunk_trace(self):
        """
        This property defines the actr parameter traces
        Trace follow the dict format: self.chunk_trace = [(chunk1, paramter1, value1), ...]
        """
        return self._chunk_trace

    @chunk_trace.setter
    def chunk_trace(self, trace):
        self._chunk_trace = trace

    @property
    def check_time(self):
        """duration from CHECK-DETECT-PROBLEM-UNLIMITED to RESPOND"""
        t = self.check_offset - self.check_onset
        if t < 0:
            return 0.0
        else:
            return t

'''
def generate_stimuli(shuffle=True, n_trials=2, valid_cue_percentage=0.5):
    "Generates stimuli according to the Boksem(2006)'s paradigm"
    congr_valid = [("CIRCLE", "LEFT", "LEFT"), ("SQUARE", "RIGHT", "RIGHT")]
    incongr_valid = [("CIRCLE", "RIGHT", "LEFT"), ("SQUARE", "LEFT", "RIGHT")]
    congr_invalid = [("CIRCLE", "LEFT", "RIGHT"), ("SQUARE", "RIGHT", "LEFT")]
    incongr_invalid = [("CIRCLE", "RIGHT", "RIGHT"), ("SQUARE", "LEFT", "LEFT")]

    valid = congr_valid * int(n_trials * (valid_cue_percentage)) + incongr_valid * int(
        n_trials * (valid_cue_percentage))
    invalid = congr_invalid * int(n_trials * (1 - valid_cue_percentage)) + incongr_invalid * int(
        n_trials * (1 - valid_cue_percentage))
    lst = valid + invalid

    if shuffle:  # Randomized if needed
        random.shuffle(lst)

    return [SimonStimulus(shape=x[0], location=x[1], cue=x[2]) for x in lst]
'''

class SimonTask:
    """A simple version of the Stroop task"""

    def __init__(self, stimuli=None, setup=False, param_set=None):
        """Initializes a Stroop task (if there are stimuli)
           motivation_value is the chunk set to goal buffer that counts for how many times
           the model attempts to retrieve until reaching correct rule
        """
        if not stimuli:
            self.stimuli = self.generate_stimuli(param_set)
            if setup:
                self.setup()
                
        # set motivation parameter and :at (production cost parameters / default:0.05)
        #self.set_motivation_parameters(param_set)
            

    def setup(self, win=None):
        """Sets up and prepares for first trial"""
        self.window = win
        self.index = 0
        self.log = []   # log behaviral
        self.phase = "fixation"
        self.trial_trace = True
        self.current_trial = SimonTrial(self.stimuli[self.index])

        # Log when production fires and when reward is delivered
        self.production_trace = []
        self.reward_trace = []

    #################### SETUP MODEL  ####################
    def setup_model(self, model="simon-motivation-model3",  param_set=None, reload=True, verbose=True):
        """Sets up model"""
        script_dir = os.path.join(os.path.dirname(os.path.realpath('../__file__')), 'script')

        # add commands
        self.add_actr_commands()

        # load model-core.lisp
        if reload:
            SimonTask.reset_trial_id()

            # schedule event of detect production/reward before loading model
            # note: if not load, no need to shceulde it again
            actr.schedule_event_now("detect-production-hook")
            actr.schedule_event_now("detect-reward-hook")

            # load model
            actr.load_act_r_model(os.path.join(script_dir, "simon-core.lisp"))
            actr.load_act_r_model(os.path.join(script_dir, "simon-base.lisp"))
            actr.load_act_r_model(os.path.join(script_dir, model + ".lisp"))

        # diable duplicate productions
        actr.pdisable('CHECK-PASS', 'RETRIEVE-INTENDED-RESPONSE')

        # load new parameter sets
        self.parameters = self.get_default_parameters()
        self.set_parameters(param_set)

        # init cost
        self.curr_cost = self.cost_function(init_cost=self.parameters["init_cost"])

        if verbose:
            print("######### SETUP MODEL " + model + " #########")
            print(">> ACT-R: ", self.parameters, "<<")


    #################### SETUP PARAMETER  ####################
    def get_parameters_name(self):
        param_names = ['seed', 'ans', 'le', 'lf', 'mas', 'bll', 'egs', 'alpha', 'imaginal-activation', 'dat']
        return param_names

    def get_parameter(self, param_name):
        """
        get parameter from current model
        :param keys: string, the parameter name (e.g. ans, bll, r1, r2)
        :return:
        """
        assert param_name in self.get_parameters_name()
        # if param_name=="r": return reward
        return actr.get_parameter_value(":" + param_name)

    def get_parameters(self, *kwargs):
        param_set = {}
        for param_name in kwargs:
            param_set[param_name] = self.get_parameter(param_name)
        return param_set

    def set_parameters(self, kwargs):
        """
        set parameter to current model
        :param kwargs: dict pair, indicating the parameter name and value (e.g. ans=0.1, r1=1, r2=-1)
        :return:
        """
        #print("start assign set_parameters", kwargs)
        #print('before', self.parameters)
        actr.hide_output()
        update_parameters = self.parameters.copy()
        # if new para given
        if kwargs:
            update_parameters.update(kwargs)
            for key, value in kwargs.items():
                if key in ["motivation", "valid_cue_percentage", "n_trials", "update_cost"]:
                    pass
                # TODO: fixed
                elif key == "init_cost":
                    actr.set_parameter_value(":dat", value)
                    #actr.spp(["PROCESS-SHAPE", "PROCESS-LOCATION", "DONT-PROCESS-SHAPE", "DONT-PROCESS-LOCATION"], ":at", value)
                else:
                    actr.set_parameter_value(':' + key, value)
            self.parameters = update_parameters

        #if no new param given
        else:
            #actr.spp(":at", self.parameters["init_cost"])
            actr.set_parameter_value(":dat", self.parameters["init_cost"])
        self.parameters["seed"] = str(self.parameters["seed"])
        actr.unhide_output()
        #print('after', self.parameters)

    def get_default_parameters(self):
        """
        default parameter sets
        """
        defaul_parameters = self.get_parameters(*self.get_parameters_name())
        defaul_other_parameters = {"motivation": 1, "init_cost": 0.05, "update_cost":False, "valid_cue_percentage":0.8, "n_trials":20}
        defaul_parameters.update(defaul_other_parameters)
        return defaul_parameters

    def generate_stimuli(self, param_set, shuffle=True, n_trials=20, valid_cue_percentage=0.5):
        "Generates stimuli according to the Boksem(2006)'s paradigm"

        try:
            n_trials = param_set["n_trials"]
        except:
            n_trials = n_trials
        try:
            valid_cue_percentage = param_set["valid_cue_percentage"]
        except:
            valid_cue_percentage = valid_cue_percentage

        congr_valid = [("CIRCLE", "LEFT", "LEFT"), ("SQUARE", "RIGHT", "RIGHT")]
        incongr_valid = [("CIRCLE", "RIGHT", "LEFT"), ("SQUARE", "LEFT", "RIGHT")]
        congr_invalid = [("CIRCLE", "LEFT", "RIGHT"), ("SQUARE", "RIGHT", "LEFT")]
        incongr_invalid = [("CIRCLE", "RIGHT", "RIGHT"), ("SQUARE", "LEFT", "LEFT")]

        valid = congr_valid * int(n_trials * (valid_cue_percentage)) + incongr_valid * int(
            n_trials * (valid_cue_percentage))
        invalid = congr_invalid * int(n_trials * (1 - valid_cue_percentage)) + incongr_invalid * int(
            n_trials * (1 - valid_cue_percentage))
        lst = valid + invalid

        if shuffle:  # Randomized if needed
            random.seed(SEED)
            random.shuffle(lst)

        return [SimonStimulus(shape=x[0], location=x[1], cue=x[2]) for x in lst]



    #################### STIMULUS DISPLAY ####################
    def fixation(self):
        #print("in fixation", self.phase)
        actr.clear_exp_window()
        item = actr.add_text_to_exp_window(self.window, "+", font_size=50,
                                           x=400, y=300,
                                           color="black")
        stim = self.current_trial.stimulus
        shape = stim.shape.upper()
        location = stim.location.upper()
        kind = stim.kind.upper()
        cue = stim.cue.upper()
        cue_kind = stim.cue_kind.upper()
        if self.trial_trace:
            print("NEW %s SIMON TRIAL: (SHAPE %s LOCATION %s CUE %s [%s])" % (kind, shape, location, cue, cue_kind))

    def cue(self):
        #print("in cue", self.phase)
        actr.clear_exp_window()
        cue = self.current_trial.stimulus.cue
        item = actr.add_visicon_features(
            ['isa', ['simon-stimulus-location', 'simon-cue'], 'kind', 'simon-cue',
             'screen-x', 400, 'screen-y', 300,
             'shape', None, 'color', 'black', 'cue', cue])

    def stimulus(self):
        #print("TEST in stimulus()", self.phase)
        actr.clear_exp_window()
        shape = self.current_trial.stimulus.shape
        location = self.current_trial.stimulus.location
        item = actr.add_visicon_features(
            ['isa', ['simon-stimulus-location', 'simon-stimulus'], 'kind', 'simon-stimulus',
             'screen-x', 200, 'screen-y', 300,
             'shape', shape, 'color', 'black', 'location', location])
        for i, shape in enumerate(SIMON_MAPPINGS):
            item = actr.add_text_to_exp_window(self.window,
                                               RESPONSE_MAPPINGS[SIMON_MAPPINGS[shape]],
                                               x=600 + i * 50,
                                               y=500)

    def done(self):
        actr.clear_exp_window()
        item = actr.add_text_to_exp_window(self.window, "done", x=400, y=300)

    def add_actr_commands(self):
        """
        This function adds all necessary act-r commands before model running
        functions:
            self.set_motivation() - set motivation parameter to goal buffer
            self.set_pcost() - set production cost parameter :at
            self.fixation() - display fixation on the screen
            self.cue() - display simon-cue on the screen and modify model's visicon features
            self.stimulus() - dispaly simon-stimulus on the screen and modify model's visicon features
            self.accept_response() - record model's response in self.log
            self.verify_reward() - check whether the model receives reward
        """
        actr.add_command("stroop-set-motivation", self.set_motivation, "Set motivation parameter for the model")
        #actr.add_command("stroop-set-pcost", self.set_pcost, "Set production cost parameter for the model")
        actr.add_command("stroop-update-cost", self.update_cost, "Update cost :dat as time goes")
        actr.add_command("stroop-update-fixation", self.fixation, "Update window: fixation")
        actr.add_command("stroop-update-cue", self.cue, "Update window: cue")
        
        actr.add_command("stroop-update-stimulus", self.stimulus, "Update window: stimulus")
        actr.add_command("stroop-accept-response", self.accept_response, "Accepts a response for the Stroop task")
        #actr.add_command("stroop-deliver-rewards", self.deliver_rewards, "Delivers a reward")
        actr.monitor_command("output-key", "stroop-accept-response")
        #actr.add_command("reward-check",self.verify_reward, "Check for a reward delivery each trial.")
        #actr.monitor_command("trigger-reward","reward-check")

        actr.add_command("detect-production-hook",self.production_hook, "Detect if a production fires")
        actr.add_command("detect-reward-hook", self.reward_hook, "Detect if a reward is delivered")

        # Note: comment this line for appropriately reloading model,
        # only schedule this event if reloading, dont scheudle if not reload
        #actr.schedule_event_now("detect-production-hook")
        #actr.schedule_event_now("detect-reward-hook")

    def remove_actr_commands(self):
        """
        This function removes all added act-r commands after model is done
        """
        actr.remove_command("stroop-set-motivation")
        #actr.remove_command("stroop-set-pcost")
        actr.remove_command("stroop-update-cost")
        actr.remove_command("stroop-update-fixation")
        actr.remove_command("stroop-update-cue")
        
        actr.remove_command_monitor("output-key", "stroop-accept-response")
        actr.remove_command("stroop-accept-response")
        #actr.remove_command_monitor("trigger-reward","reward-check")
        #actr.remove_command("reward-check")
        actr.remove_command("stroop-update-stimulus")
        #actr.remove_command("stroop-deliver-rewards")

        actr.remove_command("detect-production-hook")
        actr.remove_command("detect-reward-hook")
        
    def get_actr_goal_step(self):
        actr.hide_output()
        goal_chunk = actr.buffer_chunk('GOAL')[0]
        step = actr.chunk_slot_value(goal_chunk, 'STEP')
        actr.unhide_output()
        return step

    def update_window(self, time=200):
        #print('GOAL STEP:', self.get_actr_goal_step())
        if self.phase == "done":
            self.done()
            actr.run(time)
        #elif self.phase == "fixation":
        elif self.get_actr_goal_step() == None:
            #  MOTIVATION PARAMETER
            actr.schedule_event_now("stroop-set-motivation") 
            actr.schedule_event_relative(0.01,"stroop-update-fixation") 
            #self.set_motivation()
            #self.fixation()
            actr.run(time)
            #actr.run_full_time(10)
            #actr.run_until_time(0.15)
           
            self.phase = "cue"
            self.update_window()
        #elif self.phase == "cue":
        elif self.get_actr_goal_step() == "ATTEND-CUE":
            actr.schedule_event_relative(0.01,"stroop-update-cue") 
            #self.cue()
            actr.run(time)
            self.phase = "stimulus"
            self.update_window()
        #elif self.phase == "stimulus":
        elif self.get_actr_goal_step() == "ATTEND-STIMULUS":
            self.current_trial.onset = actr.mp_time()
            #print('self.current_trial.onset', self.current_trial.onset)
            
            # update window
            actr.schedule_event_relative(0.01,"stroop-update-stimulus") 
            #self.stimulus()

            actr.run(time)
            # DELIVER REWARD PARAMETER TO PRODUCTION
            #self.deliver_rewards()
            #actr.schedule_event_relative(0.01,"stroop-deliver-rewards")
            
            # self.current_trial.offset = actr.mp_time()

            # NEW: record the production utility
            self.current_trial.utility_trace=[self.extract_production_parameter('PROCESS-SHAPE', ':u'),
                                                 self.extract_production_parameter('PROCESS-LOCATION', ':u'),
                                                 self.extract_production_parameter('DONT-PROCESS-SHAPE', ':u'),
                                                 self.extract_production_parameter('DONT-PROCESS-LOCATION', ':u')]

            # record activation
            self.current_trial.chunk_trace = [self.extract_chunk_parameter('CIRCLE-LEFT', ':Last-Retrieval-Activation'),
                                              self.extract_chunk_parameter('SQUARE-RIGHT', ':Last-Retrieval-Activation')]

            # record cost
            '''
            self.current_trial.cost_trace=[self.extract_production_parameter('PROCESS-SHAPE', ':at'),
                                           self.extract_production_parameter('PROCESS-LOCATION', ':at'),
                                           self.extract_production_parameter('DONT-PROCESS-SHAPE', ':at'),
                                           self.extract_production_parameter('DONT-PROCESS-LOCATION', ':at')]
            '''
            actr.hide_output()
            self.current_trial.cost = actr.spp(":at")[0][0]
            actr.unhide_output()

            # record check utility trace
            self.current_trial.check_utility_trace = [self.extract_production_parameter('CHECK-PASS-M3', ':u'),
                                                      self.extract_production_parameter('DONT-CHECK', ':u')]

            # record cost

            #print('self.current_trial.offset', self.current_trial.offset)

            self.index += 1
            SimonTask.increment_trial_id()  # increment one trial
            self.log.append(self.current_trial)
            if self.index >= len(self.stimuli):
                self.phase = "done"
            else:
                self.current_trial = SimonTrial(self.stimuli[self.index])
                self.phase = "fixation"

            # update cost
            self.update_cost()

            # proceed to next trial
            self.update_window()

        # remove actr commands
        #self.remove_actr_commands()

    def accept_response(self, model, response):
        """A valid response is a key pressed during the 'stimulus' phase"""
        if self.phase == "stimulus":
            self.current_trial.response = response
            # record response time now
            self.current_trial.offset = actr.mp_time()
        #print("TEST accept_response()", self.current_trial.response, self.current_trial.stimulus)

    #################### ACT-R COMMAND ####################
    '''
    def deliver_rewards(self, verbose=False):
        """
        This function delivers reward to productions. The production name and rewards are set
        as parameter at the begining
        self.parameters['production_reward_pairs'] = [('CHECK-PASS', 0.1), ('RESPOND', -0.1)]
        """
        # print("TEST in deliver_rewards()", self.phase)
        # if (self.phase == "fixation") and self.parameters['production_reward_pairs']:
        if self.parameters['production_reward_pairs']:
            for production_name, reward_value in self.parameters['production_reward_pairs']:
                if production_name in actr.all_productions():
                    actr.spp(production_name, ':reward', reward_value)
                    if verbose: print("DELIVER REWARD:", reward_value, ">>>", production_name)
                else:
                    if verbose: print("WRONG PRODUCTION NAME", production_name, reward_value)
        else:
            if verbose: print("No reward delivered: ", self.parameters['production_reward_pairs'])
    '''
    def set_motivation(self):
        """
        This function set motivation value to goal buffer
        """
        # SET GOAL (motivation value)
        #print("TEST, in set_motivation()", self.parameters['motivation'])
        if self.phase == "fixation" and self.parameters['motivation']:
            actr.set_buffer_chunk('goal', actr.define_chunks(['isa', 'phase', 'step', 'attend-fixation',
                                                              'time-onset', actr.mp_time(),  # mental clock
                                                              'motivation', self.parameters['motivation']])[0])

    def production_hook(self, *params):
        """
        Detect the time when one of 4 production fires
        """
        fired_production=params[0]
        if fired_production in ["PROCESS-SHAPE", "PROCESS-LOCATION", "DONT-PROCESS-SHAPE", "DONT-PROCESS-LOCATION"]:
            self.production_trace.append((self.index, actr.mp_time(), fired_production))
        if fired_production == "RESPOND":
            self.current_trial.responded = True

        if ((not self.current_trial.responded) and (self.current_trial.check_count == 0) and (fired_production=="RETRIEVE-INTENDED-RESPONSE-M3")):
                #and fired_production=="CHECK-DETECT-PROBLEM-UNLIMITED"):
            self.current_trial.check_onset = actr.mp_time()
            #print("TEST check_time1", "P: ", fired_production, "check_onset:", self.current_trial.check_onset)

        # number of check is discrete variable representing control intensity
        if (not self.current_trial.responded) and (fired_production in ["CHECK-PASS-M3", "CHECK-DETECT-PROBLEM-UNLIMITED"]):
            self.current_trial.check_count += 1
            self.current_trial.check_offset = actr.mp_time()
            self.current_trial.detect_problem = True
            #print("TEST: check_count:", self.index, "P: ", fired_production, "check_count:", self.current_trial.check_count)
            #print("TEST check_time2", "P: ", fired_production, "check_offset:", self.current_trial.check_offset,
            #      "check time", self.current_trial.check_time)

        if (not self.current_trial.responded) and (self.current_trial.check_count > 0) and (self.current_trial.detect_problem) and (fired_production == "RETRIEVE-INTENDED-RESPONSE-M3"):
            self.current_trial.check_offset = actr.mp_time()
            #print("TEST check_time2", "P: ", fired_production, "check_offset:", self.current_trial.check_offset,
            #      "check time", self.current_trial.check_time)


        # time of check is continuous variable representing control intensity
        #if ((not self.current_trial.responded) and (self.current_trial.check_count > 0) and fired_production in ["CHECK-PASS-M3", "DONT-CHECK"]):
        #    self.current_trial.check_offset = actr.mp_time()
        #    print("TEST check_time2", "P: ", fired_production, "check_offset:", self.current_trial.check_offset, "check time", self.current_trial.check_time)


    def reward_hook(self, *params):
        """
        Detect the time when reward is delivered
        If return, then will replace original reward calcualtion
        """
        production = params[0]
        delivered_reward = params[1]
        passed_time = params[2]
        received_reward = delivered_reward-passed_time

        if production in ["PROCESS-SHAPE", "PROCESS-LOCATION", "DONT-PROCESS-SHAPE", "DONT-PROCESS-LOCATION"]:
            self.reward_trace.append((self.index, actr.mp_time(), production, delivered_reward, passed_time, received_reward))

        if production in ["DONT-CHECK", "CHECK-PASS-M3"]:
            if len(self.current_trial.expected_reward_check)==0:
                self.current_trial.expected_reward_check = [self.index, actr.mp_time(), production, delivered_reward, passed_time, received_reward]
            #print("++REWARD TEST", self.index, production, delivered_reward, passed_time, received_reward)
            #print("self.current.expected_reward_check", self.current_trial.expected_reward_check)
    '''
    def cost_function_old(self, old_at, c=0.001):
        """
        Define the function of cost (:dat) increases as time
        """
        return np.round(old_at + np.square(actr.mp_time() * c), 2)
        #return np.round(old_at + actr.mp_time() * c, 2)
    def update_cost_old(self, enable=False, threshold=0.5):
        """
        Update the cost for production by updating :at
        """
        #print('in update cost')
        actr.hide_output()
        old_at = actr.spp('PROCESS-SHAPE',':at')[0][0]
        new_at = self.cost_function(old_at)
        if self.phase == "fixation" and enable:
            if (new_at <= threshold) and new_at > old_at:
                print('now change cost', old_at, '>', new_at)
                actr.spp(":at", new_at)
        actr.unhide_output()
    '''
    # def cost_function1(self, a=3*1e-3, b=0.05, thresh = 0.2):
    #     """
    #     This function will change shape based on init_cost
    #     When b becomes larger, the slope becomes sharper
    #     Exponential function of cost increase as time x = (0-500) y = (0-0.5)
    #     b * exp(a*x) -b
    #
    #     a -> control slop
    #     b -> control y shift
    #     """
    #     cost = np.round((b * np.exp(a * actr.mp_time())), 2)
    #     if cost > thresh:
    #         cost = thresh
    #     return cost

    def cost_function(self, init_cost=0.05, a=0.005, b=0.005):
        """
        Updated on 6/15/2023
        y =
        """
        return np.round(init_cost - a * (1 - np.exp(b * SimonTask.get_trial_id())), 2)

    def update_cost(self):
        """
        Update :dat for all productions as time increases
        """
        if self.parameters["update_cost"]: # Turn on update cost
            old_cost = self.curr_cost
            new_cost = self.cost_function(init_cost=self.parameters["init_cost"])
            if new_cost > old_cost:
                actr.hide_output()
                actr.spp(":at", new_cost)
                actr.hide_output()
                self.curr_cost = new_cost

    @classmethod
    def increment_trial_id(cls):
        cls.trial_id += 1

    @classmethod
    def reset_trial_id(cls):
        cls.trial_id = 0

    @classmethod
    def get_trial_id(cls):
        return cls.trial_id


    #################### ACTR STATS ANALYSIS ####################
    '''
    def set_motivation_parameters(self, param_set):
        """
        This function sets motivation related parameters into a dict form
        self.parameters = {"motivation": 1, default value = 1
                           "production_reward_pairs": [("CHECK-PASS", 0.1), ("CHECK-DETECT-PROBLEM-UNLIMITED", -0.1)]}
        """
        self.parameters = {}
        # set motivation parameter 
        if param_set and ('motivation' in param_set.keys()):
            self.parameters['motivation'] = param_set['motivation']
        else:
            self.parameters['motivation'] = 1  # default value
        

        # set production_reward_pairs (only for model1)
        if param_set and ('production_reward_pairs' in param_set.keys()):
            self.parameters['production_reward_pairs'] = param_set['production_reward_pairs']
        else:
            self.parameters['production_reward_pairs'] = None
        
        # set production action time :at
        if param_set and ("at" in param_set.keys()):
            self.parameters["at"] = param_set["at"]
        else:
            self.parameters["at"] = 0.05
        actr.hide_output()
        actr.spp(':at', self.parameters["at"])
        actr.unhide_output()
        # print("TEST in set_motivation_parameters()", self.parameters)
    '''
    def run_stats(self):
        """Returns some aggregate analysis of model behavior.
        Stats are calculated only when the model successfully completes the task.
        When data are missing or the experiment is not completed, NA values
        are returned
        """
        R = dict(zip(CUE_CONDITIONS, [(0, np.nan, np.nan)] * len(CUE_CONDITIONS)))

        if len(self.log) > 0:

            cong_valid = [x for x in self.log if (x.stimulus.congruent & x.stimulus.valid)]
            incn_valid = [x for x in self.log if (x.stimulus.incongruent & x.stimulus.valid)]
            cong_invalid = [x for x in self.log if (x.stimulus.congruent & x.stimulus.invalid)]
            incn_invalid = [x for x in self.log if (x.stimulus.incongruent & x.stimulus.invalid)]

            # for cond, data in zip(CONDITIONS, [cong, incn]):
            for cond, data in zip(CUE_CONDITIONS, [cong_valid, cong_invalid, incn_valid, incn_invalid]):
                if len(data) > 0:
                    acc = sum([x.accuracy for x in data]) / len(data)
                    rt = sum([x.response_time for x in data]) / len(data)

                    R[cond] = (len(data), acc, rt)

        return R

    def print_stats(self, stats={}):
        """Pretty prints stats about the experiment"""
        for cond in stats.keys():
            n, acc, rt = stats[cond]
            print("%s (N=%d): Accuracy = %.2f, Response Times = %.2f ms" % \
                  (cond, n, acc, rt * 1000))

    def df_stats_model_outputs(self):
        df = pd.DataFrame()
        df['index'] = [i + 1 for i in range(len(self.log))]
        df['onset_time'] = [t.onset for t in self.log]
        df['accuracy'] = [t.accuracy for t in self.log]
        df['pre_trial_accuracy'] = df['accuracy'].shift(1)
        df['pre_trial_accuracy'] = df['pre_trial_accuracy'].apply(lambda x: "post-correct" 
                                                                  if x==1 else ("post-error" if x==0 else "NaN"))
        df['response_time'] = [t.response_time for t in self.log]
        df['condition_stimulus'] = [t.stimulus.kind for t in self.log]
        df['condition_cue'] = [t.stimulus.cue_kind for t in self.log]
        df['stimulus_shape'] = [t.stimulus.shape for t in self.log]
        df['stimulus_location'] = [t.stimulus.location for t in self.log]

        df['check_count'] = [t.check_count for t in self.log]
        df['check_time'] = [t.check_time for t in self.log]

        # parameter
        df['motivation'] = self.parameters["motivation"]
        df['cost'] = [t.cost for t in self.log]

        # record expected_reward_check for CHECK and NO-CHECK
        df = pd.merge(df, pd.DataFrame([t.expected_reward_check for t in self.log],
                               columns=['index', 'rewarded_time', 'production', 'delivered_reward', 'passed_time', 'received_reward']))

        # record utility for CHECK-PASS and DONT-CHECK
        df_check_utility = pd.DataFrame([[p[2] for p in t.check_utility_trace] for t in self.log],
                                        columns=['CHECK-PASS-M3', 'DONT-CHECK'],
                                        index=range(len(self.log))).reset_index().melt(id_vars='index',
                                                                                       var_name='production',
                                                                                       value_name=':u').sort_values(["index", "production"])
        df_check_utility = df_check_utility.pivot(index="index", columns="production", values=":u")
        df_check_utility.columns = ['u_check', 'u_dont_check']
        df = pd.merge(df, df_check_utility, on="index")
        
        return df
    
    #################### ACTR TRACE DATA ####################

    def extract_production_parameter(self, production_name, parameter_name):
        """
        This function will extract the parameter value of a production during model running
        """
        assert (production_name in actr.all_productions() and
                parameter_name in [':u', ':utility', ':at', ':reward', ':fixed-utility'])
        actr.hide_output()
        value = actr.spp(production_name, parameter_name)[0][0]
        actr.unhide_output()
        return (production_name, parameter_name, value)

    def extract_chunk_parameter(self, chunk_name, parameter_name):
        """
        This function will extract the parameter value of a chunk during model running
        """
        try:
            actr.hide_output()
            value = actr.sdp(chunk_name, parameter_name)[0][0]
            actr.unhide_output()
            return (chunk_name, parameter_name, value)
        except:
            print('ERROR: WRONG', chunk_name, parameter_name)
    
    def df_production_trace_outputs(self):
        """
        Process production trace data using hook function
        """
        df = pd.DataFrame(self.production_trace, columns=['index', 'firing_time', 'production'])
        df.sort_values(['index', 'firing_time'], inplace=True)
        return df

    def df_reward_trace_outputs(self):
        """
        Process production trace data using hook function
        """
        df = pd.DataFrame(self.reward_trace, columns=['index', 'rewarded_time', 'production', 'delivered_reward', 'passed_time', 'received_reward'])
        df.sort_values(['index', 'production'], inplace=True)
        return df
    
    def df_stats_trace_outputs(self, merge=True):
        """
        This function process trace data recorded in self.log
        Return: (df_chunk, df_at, df_production, df_utility)
        """
        #df_performance = self.df_stats_model_outputs()

        df_utility = pd.DataFrame([[p[2] for p in t.utility_trace] for t in self.log], 
                                  columns=['PROCESS-SHAPE', 'PROCESS-LOCATION', 'DONT-PROCESS-SHAPE', 'DONT-PROCESS-LOCATION'],
                                  index=range(len(self.log))).reset_index().melt(id_vars='index', 
                                                                                  var_name='production', 
                                                                                  value_name='u').sort_values(["index", "production"])
        ''' 
        df_at = pd.DataFrame([[p[2] for p in t.cost_trace] for t in self.log],
                           columns=['PROCESS-SHAPE', 'PROCESS-LOCATION', 'DONT-PROCESS-SHAPE', 'DONT-PROCESS-LOCATION'],
                           index=range(len(self.log))).reset_index().melt(id_vars='index', 
                                                                          var_name='production', 
                                                                          value_name=':at').sort_values(["index", "production"])
        '''

        df_chunk = pd.DataFrame([[c[2] for c in t.chunk_trace] for t in self.log],
                           columns=['CIRCLE-LEFT', 'SQUARE-RIGHT'],
                           index=range(len(self.log))).reset_index().melt(id_vars='index', 
                                                                          var_name='rule', 
                                                                          value_name='activation').sort_values(["index"])
        df_production = pd.merge_ordered(self.df_production_trace_outputs(), self.df_reward_trace_outputs(), how='outer', on=['index', 'production'])

        if merge:
            data_frames = (df_production, df_utility)
            df_merged1 = reduce(lambda left,right: pd.merge(left,right,on=['index', 'production'], how='outer'), data_frames)
            df = df_merged1.merge(df_chunk, how="left", on="index")
            #df = df_merged2.merge(df_check_utility, how="left", on="index")

            # add motivation parameter
            df['motivation'] = self.parameters['motivation']
            return df
        else:
            return (df_production, df_utility, df_chunk)
    
            


###################################################
####                SIMULATION                   ##
###################################################
def run_experiment(model="simon-motivation-model3",
                   time=200,
                   verbose=True,
                   visible=False,
                   trace=False,
                   param_set=None,
                   reload=True):
    """Runs an experiment"""

    task = SimonTask(setup=False, param_set=param_set)

    # Everytime ACT-R is reloaded, all parameters are set to init
    # Load model and add ACT-R commands
    task.setup_model(model=model, param_set=param_set, reload=reload, verbose=verbose)

    #print("TEST: in run_experiment()", task.parameters)
    win = actr.open_exp_window("* SIMON TASK *", width=800, height=600, visible=visible)
    actr.install_device(win)
    task.setup(win)
    if not trace:
        actr.set_parameter_value(":v", False)
        task.trial_trace = False
    
    # Update window
    task.update_window(time)
    task.remove_actr_commands() #NEVER REMOVE

    # Display output stats
    if verbose:
        print("-" * 80)
        task.print_stats(task.run_stats())

    # Returns the task as a Python object for further analysis of data
    return task

def run_simulation(model="simon-motivation-model3",
                   param_set=None,
                   n_simulation=1,
                   n_session=1,
                   verbose=False,
                   log=False):
    """
    Run simulation for different parameters

    """
    try:
        df_model, df_param = load_simulation(log)
        return df_model, df_param
    except:
        model_list = []
        param_list = []

        # number of simulation per parameter sets
        for j in tqdm(range(n_simulation)):
            if verbose: print("Epoch #%03d" % j)

            # number of sessions per experiment
            list_session_i = []
            list_session_i_param = []
            for i in range(n_session):
                if verbose: print("\tSession #%03d" % i)
                session_i = run_experiment(model,
                                         reload=(not i),
                                         visible=False,
                                         verbose=verbose,
                                         trace=False,
                                         param_set=param_set)
                df_session_i = session_i.df_stats_model_outputs()

                # log parameter file
                session_i_param = pd.Series(session_i.parameters)
                session_i_param['session'] = i+1

                # log session index
                df_session_i.insert(0, "session", i+1)

                list_session_i.append(df_session_i)
                list_session_i_param.append(session_i_param)

            df_epoch_j = pd.concat(list_session_i, axis=0)
            df_epoch_j_param = pd.DataFrame(list_session_i_param)

            # log simulation index
            df_epoch_j.insert(0, "epoch", j+1)

            # append all sessions
            model_list.append(df_epoch_j)
            param_list.append(df_epoch_j_param)

            # log
            if log:
                save_simulation(dir_name=log, df_model=df_epoch_j, df_param=df_epoch_j_param)


        df_model = pd.concat(model_list, axis=0)
        df_param = pd.concat(param_list, axis=0)
        return df_model, df_param

def save_simulation(dir_name, df_model, df_param):
    """
    Save simulation results
    """
    print("......>>> SAVING SIMULATION DATA <<<......")
    data_dir = os.path.join(os.path.realpath(".."), "data", dir_name + datetime.now().strftime("%y%m%d"))
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    if os.path.exists(os.path.join(data_dir, "model_output.csv")):
        mode, header = 'a', False
    else:
        mode, header = 'w', True
    df_model.to_csv(os.path.join(data_dir , "model_output.csv"), index=False,  mode=mode, header=header)

    if os.path.exists(os.path.join(data_dir, "log.csv")):
        mode, header = 'a', False
    else:
        mode, header = 'w', True
    df_param.to_csv(os.path.join(data_dir, "log.csv"), index=False,  mode=mode, header=header)

def load_simulation(dir_name):
    """
    Load Simulation data
    """

    data_dir = os.path.join(os.path.realpath(".."), "data", dir_name + datetime.now().strftime("%y%m%d"))
    if not os.path.exists(data_dir):
        print("...WRONG PATH...")
        raise ValueError
    df_model = pd.read_csv(os.path.join(data_dir, "model_output.csv"))
    df_param = pd.read_csv(os.path.join(data_dir, "log.csv"))
    print("......>>> LOAD SIMULATION DATA <<<......")
    return df_model, df_param

'''
def run_simulation(model="simon-motivation-model3", param_set=None, n_simulation=1, n_session=1, verbose=True, log=True, special_suffix=""):
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
'''

'''
def simulate_behavior(model, param_set=None, n=100, verbose=False):
    """Simulates N runs of the model"""
    accuracy_res = np.zeros((n, len(CUE_CONDITIONS)))
    rt_res = np.zeros((n, len(CUE_CONDITIONS)))
    for j in range(n):
        if verbose: print("Run #%03d" % j)
        task = run_experiment(model,
                              visible=False,
                              verbose=False,
                              trace=False,
                              param_set=param_set)
        stats = task.run_stats()
        accuracy_res[j] = np.array([stats[x][1] for x in CUE_CONDITIONS])
        rt_res[j] = np.array([stats[x][2] for x in CUE_CONDITIONS])

    return accuracy_res, rt_res


BOKSEM1 = pd.DataFrame({'condition':['incongruent', 'congruent'], 'accuracy':[1-0.153, 1-0.075], 'response_time':[0.483, 0.451]}) 
BOKSEM2 = pd.DataFrame({'condition':['invalid', 'valid'], 'accuracy':[1-0.157, 1-0.071], 'response_time':[0.488, 0.446]}) 


def stats_qc(stats):
    """Quality check for data stats. A good set of aggregagated data should have the
    following characteristics:

    1. A correct number of trials for each condition (N = 20, 20)
    2. All the data should be real numbers, and no NaN should be present
    """
    if len(stats) == 3:
        numtrials_check = True
        for condition, expected in list(zip(CONDITIONS, [20, 20])):
            if stats[condition][0] is not expected:
                numtrials_check = False

        if numtrials_check:
            # If we have the correct number of trials, let's make sure we have
            # sensible accuracies and rt values
            allvalues = []
            for condition in CONDITIONS:
                allvalues += list(stats[condition])
            print(allvalues)
            if len([x for x in allvalues if x is not np.nan]) == 9:
                return True
            else:
                return False
        else:
            return False
    else:
        return False

def model_error(model, n=2, param_set=None, observed=BOKSEM1):
    """Loss function for the model (RMSE)"""
    predicted_accuracy, predicted_rt = simulate_behavior(model, param_set, n)
    sqerr_accuracy = (predicted_accuracy.mean(axis=0) - observed["accuracy"]) ** 2
    res_accuracy = np.round(np.sqrt(np.mean(sqerr_accuracy)), 4)
    sqerr_rt = (predicted_rt.mean(axis=0) - observed['rt']) ** 2
    res_rt = np.round(np.sqrt(np.mean(sqerr_rt)), 4)
    if res_accuracy is np.nan:
        res_accuracy = 100000000
    if res_rt is np.nan:
        res_rt = 100000000
    print("MODEL (RMSE): (ACCURACY: %s \tRT: %s)" % (res_accuracy, res_rt))
    return res_accuracy, res_rt

def model_error_old(model, n=25, param_set=None, observed=BOKSEM1):
    """Loss function for the model (RMSE)"""
    predicted_accuracy, predicted_rt = simulate_behavior(model, param_set, n)
    sqerr_accuracy = (predicted_accuracy.mean(axis=0) - observed['ACCURACY_MEAN']) ** 2
    res_accuracy = np.round(np.sqrt(np.mean(sqerr_accuracy)), 4)
    sqerr_rt = (predicted_rt.mean(axis=0) - observed['RT_MEAN']) ** 2
    res_rt = np.round(np.sqrt(np.mean(sqerr_rt)), 4)
    if res_accuracy is np.nan:
        res_accuracy = 100000000
    if res_rt is np.nan:
        res_rt = 100000000
    print("MODEL (RMSE): (ACCURACY: %s \tRT: %s)" % (res_accuracy, res_rt))
    return res_accuracy, res_rt

def chery_model_error(model="simon", param_set={"ans": 0.1, "mas": 0.5}):
    return model_error(model, n=50, param_set=param_set)

# Example:

# res = opt.minimize(stroop.micah_model_error, [1.5], method='nelder-mead', options={'disp':True})


#################### LOAD MODEL CORE ####################

def load_model(model="simon-motivation-model3", param_set=None, verbose=True):
    """
    Load simon-core.lisp + simon-base.lisp + simon-motivation-modelx.lisp,and print current parameter sets
    Set parameters using param_set {"ans":0.1, "lf":0.5, "motivation":1, "production_reward_pairs":[("CHECK-PASS", 0.1), ("", 0.1)]}
    """
    curr_dir = os.path.dirname(os.path.realpath('__file__'))
    
    # load model-core.lisp + model-base.lisp 
    actr.load_act_r_model(os.path.join(curr_dir, "simon-core.lisp"))
    actr.load_act_r_model(os.path.join(curr_dir, "simon-base.lisp"))
    
    # diable duplicate productions
    actr.pdisable('CHECK-PASS', 'RETRIEVE-INTENDED-RESPONSE')
    
    # load new pramsets
    if param_set: 
        actr_param_set = param_set.copy()
        if "motivation" in param_set.keys(): actr_param_set.pop("motivation")
        if "production_reward_pairs" in param_set.keys(): actr_param_set.pop("production_reward_pairs")
        if "at" in param_set.keys(): actr_param_set.pop("at")
        set_parameters(**actr_param_set)
        
    
     # load model-x.lisp 
    actr.load_act_r_model(os.path.join(curr_dir, model+".lisp"))
    
    if verbose:
        print("######### LOADED MODEL " +model+ " #########")
        print(">> ACT-R: ", get_parameters(*get_parameters_name()), "<<") 
        try: param_set_motivation = param_set["motivation"]
        except: param_set_motivation = 1
        #try: param_set_reward = param_set["production_reward_pairs"]
        #except: param_set_reward = None
        try: param_set_at = param_set["at"]
        except: param_set_at = 0.05
        print(">> motivation param: ", param_set_motivation, "<<")
        #print(">> production_reward_pairs param: ", param_set_reward, "<<")
        print(">> production cost param (:at): ", param_set_at, "<<")
        
def check_load(model_name="simon-motivation-model3"):
    has_model = actr.current_model().lower() == model_name
    has_productions = actr.all_productions() != None
    return has_model & has_productions

#################### ACTR PARAMETER SET ####################
def get_parameters_name():
    param_names = ['seed', 'ans', 'le', 'mas', 'egs', 'alpha', 'imaginal-activation', 'motor-feature-prep-time']
    return param_names

def get_parameter(param_name):
    """
    get parameter from current model
    :param keys: string, the parameter name (e.g. ans, bll, r1, r2)
    :return:
    """
    assert param_name in ('seed', 'ans', 'le', 'mas', 'egs', 'alpha', 'imaginal-activation', 'motor-feature-prep-time', 'at')
    #if param_name=="r": return reward
    return actr.get_parameter_value(":"+param_name)

def get_parameters(*kwargs):
    param_set = {}
    for param_name in kwargs:
        param_set[param_name] = get_parameter(param_name)
    return param_set

def set_parameters(**kwargs):
    """
    set parameter to current model
    :param kwargs: dict pair, indicating the parameter name and value (e.g. ans=0.1, r1=1, r2=-1)
    :return:
    """
    for key, value in kwargs.items():
        actr.set_parameter_value(':' + key, value)

'''