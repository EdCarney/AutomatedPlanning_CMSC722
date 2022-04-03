(define (problem strips-sat-x-1)
(:domain satellite)
(:objects
	satellite0
	instrument0
	infrared0
	GroundStation0
	Star1
)
(:init
	(satellite satellite0)
	(instrument instrument0)
	(supports instrument0 infrared0)
	(calibration_target instrument0 GroundStation0)
	(on_board instrument0 satellite0)
	(power_avail satellite0)
	(pointing satellite0 GroundStation0)
	(= (data_capacity satellite0) 1000)
	(= (fuel satellite0) 146)
	(mode infrared0)
	(= (data Star1 infrared0) 123)
	(direction GroundStation0)
	(direction Star1)
	(= (slew_time Star1 GroundStation0) 30.11)
	(= (slew_time GroundStation0 Star1) 30.11)
	(= (data-stored) 0)
	(= (fuel-used) 0)
)
(:goal (and
	(have_image Star1 infrared0)
))
(:metric minimize (fuel-used))

)
