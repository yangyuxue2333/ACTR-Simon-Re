;;; ================================================================
;;; SIMON TASK MODEL
;;; ================================================================
;;; (c) 2016, Andrea Stocco, University of Washington
;;;           stocco@uw.edu
;;; (c) 2022, Modified by Cher Yang, University of Washington
;;;           chery@uw.edu
;;; ================================================================
;;; This is an ACT-R model of the Simon task. It is based on ideas
;;; heavily borrowed from Marsha Lovett's (2005) NJAMOS model of
;;; the Stroop task. It also explcitly models the competition
;;; between direct and indirect pathways of the basal ganglia as two
;;; separate set of rules, "process" and "dont-process" rules. In
;;; turn, this idea is borrowed from my model of Frank's (2004)
;;; Probabilistic Stimulus Selection Task. The same result
;;; could possibily be achieved through other means, but this
;;; solution is simple, intutitive, and permits to model competitive
;;; dynamics of the BG without changing ACT-R.
;;; ================================================================
;;;

;;;  -*- mode: LISP; Syntax: COMMON-LISP;  Base: 10 -*-
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; 
;;; Author      :Andrea Stocco 
;;; Author      :Cher Yang
;;; 
;;; 
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; 
;;; Filename    :simon-motivation-model3.lisp
;;; Version     :v3.2
;;; 
;;; Description :This declarative model simulates simon task based on Boksem (2006)'s 
;;;              paradigm. This model takes motivation parameter as mental clock: 
;;;              if the time used longer than model's motivation parameter (in sec unit), 
;;;              it would give up checking; the the time used withine the limit, the 
;;;              model would continue retrieving.
;;; 
;;; Bugs        : DONE 2/17 After 5 times run, the model will give nan responses
;;;                    2/18 Change check-detect-problem(): rather than retrieve
;;;                         once, but try to retrieve as many times until successfully
;;;                         retrieve the rule consistent with the shape on screen. 
;;;                         This gaurentee 100% correct answers for both conditions, 
;;;                         so should add a boundary to limit how many retrieval attampts.
;;;                    2/23 set goal buffer in simon_device.py rather than in simon-model3.lisp
;;;                         
;;;
;;; To do       : DONE 2/17: fix bugs because of retrival failure; add goal
;;;               DONE 2/18: DONE 1) Change whether the cue is consistent with stimulus, we
;;;                          might control for task difficulty.
;;;                          2) Add a control mechanism - whether keep retrieving:
;;;                          DONE - qualitative motivation: =1 no check; =2 check once; =3
;;;                                 check 2 times... 
;;;                          - quantative control: no check vs. go check unlimited time
;;;                          DONE 3) Add a reward delivery mechanism - when check-failed
;;;                                  deliver negative rewards, when check passed, positive.
;;;                          DONE 4) Use Boksem's paradigm, add cue
;;;                    2/23 1) Following Mareka's mind-windering model? When task-relevant goal
;;;                          is retrieved
;;;                         DONE 2) Goal buffer delivers reward
;;;                         DONE 3) GOAL buffer check-time, rather than how many times one retrieves
;;;                    2/25 1) Encode feedback - post-error-slow? After negative feedback, adjust 
;;;                         motivation parameter - longer duration for checking, or more times of 
;;;                         checking
;;;                    3/03 Add temporal buffer to inccorporate reward and time
;;; 
;;; ----- History -----
;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;
;;; General Docs:
;;; 
;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;
;;; Public API:
;;;
;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;
;;; Design Choices:
;;; 
;;; Task description 
;;; The model looks at the fixation cross on the screen and prepare wm. Once 
;;; the simon-stimulus occurs, it would encode the stimulus in WM.
;;; Four productions compete: process-shape(), process-location(), 
;;; dont-process-shape(), dont-process-location(). 
;;; The model retrieves simon rule from LTM
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; 
;;; Productions: 
;;; p retrieve-intended-response-m3 ()
;;; p check-pass-m3 ()
;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;


;;; ----------------------------------------------------------------
;;; RESPONSE SELECTION
;;; ----------------------------------------------------------------
;;; The more responds by harvesting the most active Simon rule.
;;; Thus, response is guided by spreading activation from WM.
;;; A one-time check routine is also granted.
;;; ----------------------------------------------------------------

(p retrieve-intended-response-m2
   "Retrieves the relevant part of the Simon Task rule"
   =visual>
     kind simon-stimulus
     shape =SHAPE
     
   =imaginal>
     state process
   - value1 nil
   - value2 nil
   
   ?retrieval>
     state free
     buffer empty

   =goal>
     isa        phase
     step       attend-stimulus
     updated-motivation   =MOT
     time-onset   =TIME
==>
   =visual>   ; Keep visual
   =imaginal> ; Keep WM
   +retrieval>
     kind simon-rule
     has-motor-response yes
   !bind!       =CURRTIME (mp-time)
   !bind!       =DURATION (- =CURRTIME =TIME)
   !bind! =DIFF (- =MOT =DURATION)
   *goal>
     step       retrieve-rule
     updated-motivation   =DIFF

   ;!output! (in retrieve-intended-response() the motivation val is =MOT duration value is =DURATION new motivation val is =DIFF)
   ;;;!output! (in retrieve-intended-response()  (mp-time-ms))
)

(p check-pass-m2
   "Makes sure the response is compatible with the rules"
   =visual>
     shape =SHAPE
   
   =retrieval>
     kind  simon-rule
     shape =SHAPE

   =imaginal>
     state process
     - checked yes
   
   ?imaginal>
     state free

   =goal>
     isa        phase
     step       retrieve-rule
     updated-motivation   =MOT
     > updated-motivation   0 ;;; compete with dont-check, higher utility fires
==>
   *goal>
     step       check-rule
   =visual>
   =retrieval>
   =imaginal>
     ;value2 nil
     checked yes
   ;!output! (in check-pass() motivation is =MOT)
)
