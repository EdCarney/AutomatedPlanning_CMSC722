
(define (domain satellite)
     (:requirements :typing :equality)
     (:types
          satellite direction instrument mode
     )
     (:predicates
          (on_board ?i ?s)
          (supports ?i ?m)
          (pointing ?s ?d)
          (power_avail ?s)
          (power_on ?i)
          (calibrated ?i)
          (have_image ?d ?m)
          (calibration_target ?i ?d)
          (satellite ?s)
          (instrument ?i)
          (mode ?m)
          (direction ?d)
     )

     (:functions
          (data_capacity ?s)
          (data ?d ?m)
          (slew_time ?a ?b)
          (data-stored)
          (fuel ?s)
          (fuel-used)
     )

     (:action turn_to
          :parameters (?s ?d_new ?d_prev)
          :precondition (and (pointing ?s ?d_prev)
               (not (= ?d_new ?d_prev))
               (>= (fuel ?s) (slew_time ?d_new ?d_prev))
          )
          :effect (and (pointing ?s ?d_new)
               (not (pointing ?s ?d_prev))
               (decrease (fuel ?s) (slew_time ?d_new ?d_prev))
               (increase (fuel-used) (slew_time ?d_new ?d_prev))
          )
     )

     (:action switch_on
          :parameters (?i ?s)

          :precondition (and (on_board ?i ?s)
               (power_avail ?s)
          )
          :effect (and (power_on ?i)
               (not (calibrated ?i))
               (not (power_avail ?s))
          )

     )

     (:action switch_off
          :parameters (?i ?s)

          :precondition (and (on_board ?i ?s)
               (power_on ?i)
          )
          :effect (and (not (power_on ?i))
               (power_avail ?s)
          )
     )

     (:action calibrate
          :parameters (?s ?i ?d)
          :precondition (and (on_board ?i ?s)
               (calibration_target ?i ?d)
               (pointing ?s ?d)
               (power_on ?i)
          )
          :effect (calibrated ?i)
     )

     (:action take_image
          :parameters (?s ?d ?i ?m)
          :precondition (and (calibrated ?i)
               (on_board ?i ?s)
               (supports ?i ?m)
               (power_on ?i)
               (pointing ?s ?d)
               (power_on ?i)
               (>= (data_capacity ?s) (data ?d ?m))
          )
          :effect (and (decrease (data_capacity ?s) (data ?d ?m)) (have_image ?d ?m)
               (increase (data-stored) (data ?d ?m)))
     )
)