(define(problem blocks-test-10)(:domain blocks)(:objects b1 b2 b3 b4 b5 b6 b7 b8 b9 b10)(:init(on b1 b5)(clear b1)(on b2 b4)(on b3 b6)(on b4 b9)(on b5 b2)(on b6 b10)(on b7 b3)(clear b7)(ontable b8)(on b9 b8)(ontable b10)(handempty))(:goal (and(on b1 b4)(on b2 b10)(on b3 b6)(ontable b4)(on b5 b2)(clear b5)(on b6 b8)(ontable b7)(on b8 b7)(on b9 b1)(clear b9)(on b10 b3)(handempty))))