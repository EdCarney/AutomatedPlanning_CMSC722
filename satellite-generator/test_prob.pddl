(define (problem strips-sat-x-1)
(:domain satellite)
(:objects
	satellite0
	instrument0
	satellite1
	instrument1
	thermograph1
	infrared0
	Star0
	Star1
	Phenomenon2
	Phenomenon3
)
(:init
	(satellite satellite0)
	(instrument instrument0)
	(supports instrument0 thermograph1)
	(calibration_target instrument0 Star0)
	(on_board instrument0 satellite0)
	(power_avail satellite0)
	(pointing satellite0 Phenomenon2)
	(satellite satellite1)
	(instrument instrument1)
	(supports instrument1 infrared0)
	(supports instrument1 thermograph1)
	(calibration_target instrument1 Star1)
	(on_board instrument1 satellite1)
	(power_avail satellite1)
	(pointing satellite1 Star1)
	(mode thermograph1)
	(mode infrared0)
	(direction Star0)
	(direction Star1)
	(direction Phenomenon2)
	(direction Phenomenon3)
)
(:goal (and
	(have_image Phenomenon2 thermograph1)
	(have_image Phenomenon3 thermograph1)
))

)
