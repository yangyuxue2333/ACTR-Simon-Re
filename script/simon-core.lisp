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
;;; Author      :Andrea Stocco (Modified by Cher Yang)
;;; 
;;; 
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; 
;;; Filename    :simon-core.lisp
;;; Version     :v3.1
;;; 
;;; Description :This lisp script only deals with parameter setting. Main doc can 
;;;              be found in simon-body.lisp
;;; 
;;; Bugs        :
;;;
;;;
;;; To do       : 
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
;;; 
;;; p find-screen ()
;;; p prepare-wm ()
;;; p process-shape()
;;; p dont-process-shape()
;;; p process-location ()
;;; p dont-process-location ()
;;; p check-pass()
;;; p check-detect-problem ()
;;; p respond()
;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(clear-all)
(define-model simon-motivation-model
    (sgp :seed (100 0)
         :er t
         :esc t
         :ncnar t ;normalize chunk names after run
         :model-warnings nil
         :ans 0.5
         :auto-attend t
         :le 0.63
         ;:lf 0.1
         :bll 0.1
         :mas 4.0
         :ul t
         :egs 0.1
         :alpha 0.4
         :imaginal-activation 3.0
         :motor-feature-prep-time 0.01
         :dat 0.05  ; default action time for all productions
         :show-focus t 
         :needs-mouse t
         :model-warnings nil
         ;:v t
         ;:trace-detail low
         ;:ult t
         ;:act t
         :trace-filter production-firing-only
         ;:pct t
         ;:blt t
         :reward-hook "detect-reward-hook"
         :cycle-hook "detect-production-hook"

    )
)
