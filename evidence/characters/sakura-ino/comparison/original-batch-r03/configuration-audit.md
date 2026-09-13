# Original batch r03 configuration audit

The retained Flash builds used p1 helper `松本` (`jinye.swf`) and p2 helper `魂` (`kon.swf`). The matching GameWorld fixtures omitted both selection fields, so the harness loaded its default p1 helper `我爱罗` while the source capture exercised `jinye`. The r03 comparator reports are preserved and relabeled `invalid_comparison_configuration`; they are not runtime parity failures.

The corrected r04 fixtures add explicit `p1_helper: jinye` and `p2_helper: kon`. Their fighter selection, input windows, positions, energy, frame count, and source thresholds are unchanged. Original trace files were not edited.
