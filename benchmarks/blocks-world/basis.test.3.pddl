(define (problem blocks-world-5-1)
    (:domain blocks)
    (:objects
        b1 b2 b3
    )

    (:init
        (on b2 b1)
        (ontable b1)
        (ontable b3)
        (clear b2)
        (clear b3)
        (handempty)
    )

    (:goal
        (and
            (on b1 b2)
            (ontable b2)
            (ontable b3)
            (clear b1)
            (clear b3)
            (handempty)
        )
    )
)