(clear-all)
(define-model mini-experiment

;;; ----- DEFINE PARAMETERS
(sgp ;:seed (100 0)
     :er t
     :esc t
     :ul t
     :v nil
     ;:ult t
     ;:act t
     :cmdt nil
     :trace-detail high
     :trace-filter production-firing-only ;trigger-reward
     :egs 0.5
     :alpha 0.4
     :ans 0.5
     :bll 0.5
     :le 0.63
     :cycle-hook "production-hook"
     :utility-hook "utility-hook"
     :reward-hook "reward-hook"
     )

;;; ----- DEFINE CHUNK-TYPE
(chunk-type phase
      step
      motivation
      time-onset        ;;; mental clock
      time-duration)    ;;; mental clock

(chunk-type simon-rule
  kind
  has-motor-response
  shape
  hand
  dimension)

;;; ----- DEFINE CHUNK IN DM
(add-dm 
    (start ISA chunk)
    (end ISA chunk)
    (yes ISA chunk)
    (deliver-rewards ISA chunk)
    (SHAPE ISA chunk)
    (CIRCLE ISA chunk) 
    (SQUARE ISA chunk) 
    (SIMON-RULE ISA chunk)
    (retrieve-rule ISA chunk) 
 
 ;;; --------- The Simon Task rules ---------
    (circle-left isa simon-rule
         kind simon-rule
         has-motor-response yes
         hand left
         shape circle
         dimension shape)

    (square-right isa simon-rule
          kind simon-rule
          has-motor-response yes
          hand right
          shape square
          dimension shape)
)

;;; ----- DEFINE PRODUCTIONS
(p start-trial
    ?goal>
       buffer empty
       state free
==>
    +goal>
       isa phase
       step start
       motivation 1
    +temporal> 
       isa time
       ticks 0
   !bind!       =CURRTIME (mp-time)
   ;!output! (CURRTIME is =CURRTIME )
)
    
(p p1
   ?goal>
       state free
   =goal>
       isa phase
       step start
       motivation =MOT
   =temporal>
       isa time
       ticks =TICKS
==>
   *goal>
       step retrieve-rule
   ;!eval! (trigger-reward =TICKS)
   ;!output! (in p1() motivation value is =MOT ticks value is =TICKS)
)

(p p2
   ?goal>
       state free
   =goal>
       isa phase
       step start
       motivation =MOT
   =temporal>
       isa time
       ticks =TICKS
==>
   *goal>
       step retrieve-rule
   ;!eval! (trigger-reward =TICKS)
   ;!output! (in p2() motivation value is =MOT ticks value is =TICKS)
)
    
(p p3
   ?goal>
       state free
   =goal>
       isa phase
       step start
       motivation =MOT
   =temporal>
       isa time
       ticks =TICKS
==>
   *goal>
       step retrieve-rule
   ;!eval! (trigger-reward =TICKS)
   ;!output! (in p2() motivation value is =MOT ticks value is =TICKS)
)

(p p4
   ?goal>
       state free
   =goal>
       isa phase
       step start
       motivation =MOT
   =temporal>
       isa time
       ticks =TICKS
==>
   *goal>
       step retrieve-rule
   ;!eval! (trigger-reward =TICKS)
   ;!output! (in p2() motivation value is =MOT ticks value is =TICKS)
)
    
(p p5
   ?goal>
       state free
   =goal>
       isa phase
       step start
       motivation =MOT
   =temporal>
       isa time
       ticks =TICKS
==>
   *goal>
       step retrieve-rule
)
    
(p p6
   ?goal>
       state free
   =goal>
       isa phase
       step start
       motivation =MOT
   =temporal>
       isa time
       ticks =TICKS
==>
   *goal>
       step retrieve-rule
)

(p p7
   ?goal>
       state free
   =goal>
       isa phase
       step start
       motivation =MOT
   =temporal>
       isa time
       ticks =TICKS
==>
   *goal>
       step retrieve-rule
)
    
(p p8
   ?goal>
       state free
   =goal>
       isa phase
       step start
       motivation =MOT
   =temporal>
       isa time
       ticks =TICKS
==>
   *goal>
       step retrieve-rule
)
    
(p p9
   ?goal>
       state free
   =goal>
       isa phase
       step start
       motivation =MOT
   =temporal>
       isa time
       ticks =TICKS
==>
   *goal>
       step retrieve-rule
)

(p p10
   ?goal>
       state free
   =goal>
       isa phase
       step start
       motivation =MOT
   =temporal>
       isa time
       ticks =TICKS
==>
   *goal>
       step retrieve-rule
)

(p retrieve-rule
    ?goal>
       state free
    =goal>
       isa phase
       step retrieve-rule
    =temporal>
       isa time
       ticks =TICKS
 ==>
   *goal>
       step deliver-rewards
   +retrieval>
     kind simon-rule
     has-motor-response yes
   ;!eval! (trigger-reward (* 0.1 =TICKS))
   ;!output! (in deliver-rewards ticks value is =TICKS)
)
    
(p retrieve-yes
   ?goal>
       state free
    =goal>
       isa phase
       step deliver-rewards
    =retrieval>
        kind  simon-rule
        shape =SHAPE
==> 
   *goal>
       step end
   ;!eval! (trigger-reward (* 0.1 =TICKS))
   ;!eval! (spp p1 :at 0.1)
   ;!eval! (sgp :reward-hook "bg-reward-hook")
   ;!output! ( =(monitor-act-r-command "print-warning" "model-output"))
)
    
(p retrieve-failure
    ?goal>
       state free
    ?retrieval>
      buffer   failure
    =goal>
       isa phase
       step deliver-rewards
    =temporal>
       isa time
       ticks =TICKS
==>
    *goal>
       step end
)

(p skip-retrieval
    ?goal>
       state free
    =goal>
       isa phase
       step retrieve-rule
    =temporal>
       isa time
       ticks =TICKS
 ==>
   *goal>
       step end
)
    
;;; ----- DONE
(p done 
   ?goal>
     state          free
   =goal>
     isa   phase
     step  end
   =temporal>
       isa time
       ticks =TICKS
==>
   -goal>
   !bind!       =CURRTIME (mp-time)
   ;!output! (CURRTIME is =CURRTIME )
   ;!stop!
   ;!eval! (trigger-reward 1)
)

;(spp (p1 :at 0.0101 );:reward .1)
;     (p2 :at 0.0202 );:reward .2)
;     (p3 :at 0.0305 );:reward .3)
;     (p4 :at 0.0408 );:reward .4)
)

