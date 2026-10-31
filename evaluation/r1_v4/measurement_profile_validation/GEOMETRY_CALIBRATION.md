# Geometry findings and numerical limits

The five protected objects have 22 declared collision BOX pieces; six table pieces bring this profile to 28. Root IDs and complete collision unions are retained. World geom_xpos/geom_xmat supply poses; half-sizes come from the corrected serialized-model descriptor. Other native geometry types are not approximated as boxes.

Across1,312 snapshots the retained guard observes maximum position residual 2.220446049250313e-16m and rotation-component residual 2.55351295663786e-15. Existing allowances are 3.410605131648481e-13m and 1.1368683772161603e-13 respectively. These are arithmetic consistency budgets, not contact tolerances or physical uncertainty.

## Computation envelope

For p+R*(sign*half_size), each product and endpoint sum is rounded outward using adjacent binary64 values. This encloses the expression over supplied exact binary64 inputs; overflow is rejected. Union bounds use minima of lower and maxima of upper endpoints across all pieces. Displacement intervals subtract outward endpoints without assuming independent errors. The Fraction oracle passes 648 coordinates in 27 constructed BOX cases. These are analytical checks, not physical reference cases.

Observed interval widths range 3.3306690738754696e-16 to 1.5543122344752192e-15m. The maximum is a sample statistic, not a universal clearance band. Use the per-calculation interval. Physical input uncertainty stays null. Arithmetic width cannot absorb unknown shape, pose, serialization or phase uncertainty.

## Roots and surfaces

Root-to-lower collision extent ranges 0.00871–0.07456889221574342m; upper extent reaches 0.07320131043876144m. Root height is neither collision bottom nor center of mass. All corresponding vertices/pieces remain represented; vertex dz is a measurement indicator, not a fall or handling classifier.

Pieces 10–14 have recorded AABB upper z 0.43676000000000015m; lower structure 15 reaches 0.4129800000000001m. Do not collapse these into one universal height or omit 15. Face-axis residuals 2.22e-16–4.44e-16 are consistent with numerical axis alignment under the retained budget, not independent validation of a physical support profile.

## Input/model uncertainty

Native geom_size was not saved as a per-frame measurement. Descriptors use serialized XML sizes. Prior rotation serialization diagnostics show rounded XML/runtime differences; recorded world transforms are preferable to recompiling rounded rotations. Those source-specific discrepancy studies do not supply a universal bound for every shape/model. Native-size/serialization and physical-reference uncertainty cannot become zero because recomposition passes.

P01/P02 justify computation-level methods only. Physical BOX tolerance and surface-boundary uncertainty remain BLOCKED_ON_EVIDENCE. Independent model/geometry checks, uncertainty provenance and a validated support-face profile are prerequisites for empirical geometry admission. No edge, contact or clearance band is fitted.
