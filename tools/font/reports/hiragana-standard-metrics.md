# Version 1.025 — standard Japanese size normalization

Shape remains entirely from the complete maintainer Master v2. Absolute optical size is normalized against standard Japanese metrics; production 1.024 supplies continuity. The family renderer alone supplies stroke weight. No external font outline, curve, point, component or stroke is retained or installed. External font binaries were read from temporary files outside the repository.

“Optical” measurements here mean actual ink bounding-box extent and its midpoint, not an ink-mass centroid. Coordinates are divided by each font’s UPM before comparison. Baseline bottom/top, normalized bounds and full-width cell occupancy are retained in the [scalar reference snapshot](../references/hiragana-metric-references.json).

## References

- [Noto Sans CJK JP Regular](https://github.com/notofonts/noto-cjk/blob/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf), Version 2.004;hotconv 1.0.118;makeotfexe 2.5.65603, UPM 1000; SHA256 `68a3fc98800b2a27b371f2fb79991daf3633bd89309d4ffaa6946fd587f375b5`.
- [Source Han Sans JP Regular](https://github.com/adobe-fonts/source-han-sans/blob/release/SubsetOTF/JP/SourceHanSansJP-Regular.otf), Version 2.005;addfeatures 5.0.0b21, UPM 1000; SHA256 `40d1b760d1135539f6b6e0ee2b9f415de6d97576f7676840b06306c7c190c074`.

Continuity reference: QuanFangwei Supplement Script Version 1.024, UPM 1024, immutable base `d89ee8b2b5f4c858e5dade853972194892037f93:assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf`; SHA256 `c32cea769cd285be642b3358a54049ef7f11449de06e3773d3ade4d5cf9548b6`.

Noto and Source Han have identical measured width, height and box centers for all 46 glyphs (maximum difference 0 em). They count as one external reference group, paired with the independent production font.

## Target and fit policy

For each character, target height and x/y box centers are the median of the external group and production 1.024. Width is a sanity range: 90% of the smaller reference width through 110% of the larger, capped at `(960−40)/1024` em. Height has a ±5% envelope and centers a ±0.02 em envelope; actual fit tolerances are tighter: height ≤1.5 font units, centers ≤1 unit from target.

One uniform center-line scale is fitted against actual rendered height, followed by dx/dy to the target center. Pressure is not scaled, so the renderer retains the established handwriting weight. Photo coordinates retain only relative gesture/aspect information; photo pixels never set absolute glyph size. All 46 fits are uniform: **no non-uniform exceptions**. Every advance stays **960 units at 1024 UPM**.

The large bases are normalized before all 12 small forms are derived. The three Hiragana yōon translations are recalibrated afterward to the existing `(180,24)` ink anchor; Katakana offsets and topology remain unchanged.

## Family size gate

| Metric (em) | Median | Minimum | Maximum |
|---|---:|---:|---:|
| width_em | 0.633301 | 0.365234 | 0.841797 |
| height_em | 0.702637 | 0.482422 | 0.783203 |
| center_x_em | 0.488770 | 0.466309 | 0.530762 |
| center_y_em | 0.359863 | 0.338379 | 0.374023 |

Flags are triggered by height below 75% of the family median, width below 70%, or width above 140%. The following flags were explicitly reviewed against the handwriting and individual reference envelope:

- **う**: narrow relative to family median. Tall narrow main gesture from the handwriting; width remains within the reference envelope.
- **く**: narrow relative to family median. Narrow angled handwritten gesture; width remains within the reference envelope.
- **つ**: short relative to family median. Shallow handwritten bowl; its per-character standard/production height target takes precedence over a family median.
- **へ**: short relative to family median. Shallow handwritten arch; its per-character standard/production height target takes precedence over a family median.
- **り**: narrow relative to family median. Narrow two-stroke handwriting; width remains within the reference envelope.

## Per-character comparison

Ratios are `(width, height, center-x, center-y)` in em. dx/dy are QuanFangwei font units; scale applies uniformly to the manually authored source. Both external fonts are listed separately in the [complete CSV](hiragana-standard-metrics.csv); their identical values are grouped here.

| Glyph | Reference font | UPM | Ref width | Ref height | Ref cx | Ref cy | Old QFW ratios | New QFW ratios | Scale | dx | dy | Δheight / Δcx / Δcy em |
|---|---|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---|
| あ | Noto / Source Han JP Regular | 1000 | 0.7960 | 0.8440 | 0.5070 | 0.3720 | 0.5635 / 0.6621 / 0.4673 / 0.3525 | 0.6318 / 0.7529 / 0.4868 / 0.3628 | 1.143952 | +19.3340 | +9.4640 | -0.000125 / -0.000326 / +0.000523 |
| い | Noto / Source Han JP Regular | 1000 | 0.7940 | 0.7090 | 0.5230 | 0.3455 | 0.6738 / 0.5557 / 0.4688 / 0.3491 | 0.7617 / 0.6318 / 0.4961 / 0.3472 | 1.169280 | +29.7760 | -3.3540 | -0.000496 / +0.000219 / -0.000143 |
| う | Noto / Source Han JP Regular | 1000 | 0.6390 | 0.8310 | 0.4855 | 0.3675 | 0.3096 / 0.6387 / 0.4683 / 0.3525 | 0.3652 / 0.7354 / 0.4766 / 0.3599 | 1.113119 | +6.8260 | +6.6600 | +0.000516 / -0.000318 / -0.000156 |
| え | Noto / Source Han JP Regular | 1000 | 0.7920 | 0.8310 | 0.5120 | 0.3735 | 0.4434 / 0.5703 / 0.4658 / 0.3486 | 0.5703 / 0.7002 / 0.4893 / 0.3608 | 1.056177 | +21.1440 | +7.2320 | -0.000461 / +0.000348 / -0.000227 |
| お | Noto / Source Han JP Regular | 1000 | 0.8450 | 0.8310 | 0.5275 | 0.3835 | 0.6035 / 0.6602 / 0.4678 / 0.3525 | 0.6865 / 0.7451 / 0.4976 / 0.3677 | 1.128032 | +30.0800 | +15.3520 | -0.000461 / -0.000078 / -0.000344 |
| か | Noto / Source Han JP Regular | 1000 | 0.8870 | 0.8210 | 0.5215 | 0.3795 | 0.6416 / 0.4785 / 0.4683 / 0.3457 | 0.6084 / 0.6504 / 0.4946 / 0.3623 | 0.973462 | +27.2580 | +9.8040 | +0.000633 / -0.000252 / -0.000297 |
| き | Noto / Source Han JP Regular | 1000 | 0.6990 | 0.8460 | 0.5095 | 0.3750 | 0.4365 / 0.6650 / 0.4683 / 0.3521 | 0.4951 / 0.7559 / 0.4888 / 0.3643 | 1.141468 | +21.6140 | +11.2500 | +0.000340 / -0.000111 / +0.000732 |
| く | Noto / Source Han JP Regular | 1000 | 0.5211 | 0.8690 | 0.4655 | 0.3695 | 0.3838 / 0.5059 / 0.4683 / 0.3486 | 0.3779 / 0.6875 / 0.4663 / 0.3594 | 1.033786 | +0.5713 | +6.6840 | +0.000070 / -0.000558 / +0.000309 |
| け | Noto / Source Han JP Regular | 1000 | 0.8030 | 0.8390 | 0.5205 | 0.3605 | 0.4531 / 0.6377 / 0.4961 / 0.3247 | 0.6777 / 0.7393 / 0.5088 / 0.3423 | 1.116316 | +41.4960 | -11.1740 | +0.000910 / +0.000492 / -0.000318 |
| こ | Noto / Source Han JP Regular | 1000 | 0.6620 | 0.7280 | 0.5040 | 0.3390 | 0.4697 / 0.5430 / 0.4917 / 0.3477 | 0.6318 / 0.6348 / 0.4976 / 0.3438 | 1.009348 | +30.2980 | -9.9320 | -0.000719 / -0.000291 / +0.000422 |
| さ | Noto / Source Han JP Regular | 1000 | 0.7040 | 0.8400 | 0.5100 | 0.3780 | 0.4365 / 0.6631 / 0.4683 / 0.3521 | 0.4893 / 0.7510 / 0.4888 / 0.3647 | 1.135719 | +21.3700 | +11.7860 | -0.000566 / -0.000361 / -0.000279 |
| し | Noto / Source Han JP Regular | 1000 | 0.6610 | 0.8310 | 0.5675 | 0.3645 | 0.4482 / 0.5703 / 0.4663 / 0.3496 | 0.5283 / 0.7002 / 0.5171 / 0.3569 | 1.046484 | +50.3100 | +6.6240 | -0.000461 / +0.000186 / -0.000121 |
| す | Noto / Source Han JP Regular | 1000 | 0.8330 | 0.8460 | 0.5125 | 0.3690 | 0.4893 / 0.6689 / 0.5483 / 0.3188 | 0.5615 / 0.7568 / 0.5308 / 0.3442 | 1.148392 | +64.1500 | -9.8220 | -0.000637 / +0.000342 / +0.000314 |
| せ | Noto / Source Han JP Regular | 1000 | 0.8770 | 0.7880 | 0.4835 | 0.3770 | 0.4795 / 0.5625 / 0.4712 / 0.3477 | 0.7930 / 0.6748 / 0.4775 / 0.3628 | 1.241908 | +9.8020 | +10.5240 | -0.000445 / +0.000193 / +0.000465 |
| そ | Noto / Source Han JP Regular | 1000 | 0.7750 | 0.8120 | 0.4895 | 0.3620 | 0.4775 / 0.5127 / 0.4712 / 0.3491 | 0.5078 / 0.6631 / 0.4805 / 0.3560 | 0.994174 | +17.3740 | +3.0852 | +0.000721 / +0.000123 / +0.000405 |
| た | Noto / Source Han JP Regular | 1000 | 0.8070 | 0.8310 | 0.5045 | 0.3795 | 0.4922 / 0.6816 / 0.4668 / 0.3486 | 0.5391 / 0.7559 / 0.4854 / 0.3633 | 1.142265 | +17.8040 | +10.8040 | -0.000461 / -0.000297 / -0.000785 |
| ち | Noto / Source Han JP Regular | 1000 | 0.7380 | 0.8273 | 0.4810 | 0.3744 | 0.4121 / 0.6846 / 0.4668 / 0.3501 | 0.5723 / 0.7568 / 0.4736 / 0.3618 | 1.142458 | +4.7720 | +8.9180 | +0.000902 / -0.000266 / -0.000408 |
| つ | Noto / Source Han JP Regular | 1000 | 0.8350 | 0.6360 | 0.4905 | 0.3320 | 0.4688 / 0.4053 / 0.4678 / 0.3442 | 0.5967 / 0.5205 / 0.4790 / 0.3384 | 0.932826 | +11.1360 | +8.7340 | -0.000129 / -0.000133 / +0.000260 |
| て | Noto / Source Han JP Regular | 1000 | 0.7970 | 0.7590 | 0.4835 | 0.3485 | 0.5088 / 0.5957 / 0.4683 / 0.3496 | 0.5615 / 0.6777 / 0.4761 / 0.3496 | 1.044730 | +10.8020 | -5.5680 | +0.000383 / +0.000193 / +0.000555 |
| と | Noto / Source Han JP Regular | 1000 | 0.6400 | 0.8060 | 0.5210 | 0.3750 | 0.4746 / 0.5703 / 0.4678 / 0.3223 | 0.6348 / 0.6875 / 0.4941 / 0.3486 | 1.103820 | +26.7520 | +11.5000 | -0.000656 / -0.000246 / +0.000000 |
| な | Noto / Source Han JP Regular | 1000 | 0.8380 | 0.8530 | 0.5130 | 0.3755 | 0.5254 / 0.6143 / 0.4658 / 0.3501 | 0.6279 / 0.7334 / 0.4897 / 0.3628 | 1.104894 | +22.1560 | +11.0060 | -0.000230 / +0.000336 / -0.000006 |
| に | Noto / Source Han JP Regular | 1000 | 0.7750 | 0.7930 | 0.5115 | 0.3635 | 0.5801 / 0.5420 / 0.4668 / 0.3472 | 0.7090 / 0.6670 / 0.4893 / 0.3550 | 1.066407 | +22.3880 | +1.8620 | -0.000504 / +0.000109 / -0.000354 |
| ぬ | Noto / Source Han JP Regular | 1000 | 0.8910 | 0.7970 | 0.5205 | 0.3845 | 0.6416 / 0.4912 / 0.4673 / 0.3501 | 0.7783 / 0.6436 / 0.4937 / 0.3677 | 1.174190 | +28.2460 | +16.1140 | -0.000551 / -0.000240 / +0.000377 |
| ね | Noto / Source Han JP Regular | 1000 | 0.9180 | 0.8320 | 0.5140 | 0.3780 | 0.6064 / 0.7021 / 0.4683 / 0.3501 | 0.7920 / 0.7676 / 0.4907 / 0.3643 | 1.201910 | +23.4180 | +12.2860 | +0.000504 / -0.000408 / +0.000209 |
| の | Noto / Source Han JP Regular | 1000 | 0.8200 | 0.7490 | 0.4980 | 0.3435 | 0.5459 / 0.4102 / 0.4692 / 0.3477 | 0.6455 / 0.5801 / 0.4839 / 0.3457 | 0.959665 | +17.7260 | -7.6280 | +0.000500 / +0.000268 / +0.000125 |
| は | Noto / Source Han JP Regular | 1000 | 0.8350 | 0.8080 | 0.5325 | 0.3670 | 0.5244 / 0.6025 / 0.4663 / 0.3462 | 0.7012 / 0.7051 / 0.5000 / 0.3564 | 1.084400 | +34.3900 | +7.1540 | -0.000191 / +0.000596 / -0.000150 |
| ひ | Noto / Source Han JP Regular | 1000 | 0.8370 | 0.7890 | 0.5275 | 0.3445 | 0.5703 / 0.5244 / 0.4658 / 0.3481 | 0.8242 / 0.6562 / 0.4971 / 0.3467 | 1.253447 | +29.5800 | -5.3660 | -0.000457 / +0.000410 / +0.000357 |
| ふ | Noto / Source Han JP Regular | 1000 | 0.9200 | 0.8020 | 0.5020 | 0.3720 | 0.6064 / 0.5742 / 0.4663 / 0.3496 | 0.7568 / 0.6875 / 0.4839 / 0.3604 | 1.183480 | +16.2740 | +7.9640 | -0.000609 / -0.000268 / -0.000453 |
| へ | Noto / Source Han JP Regular | 1000 | 0.8950 | 0.5984 | 0.5035 | 0.3362 | 0.5342 / 0.3672 / 0.4683 / 0.3584 | 0.7764 / 0.4824 / 0.4858 / 0.3467 | 1.177765 | +18.0420 | +11.6421 | -0.000387 / -0.000041 / -0.000627 |
| ほ | Noto / Source Han JP Regular | 1000 | 0.8310 | 0.8030 | 0.5305 | 0.3645 | 0.5557 / 0.4326 / 0.4683 / 0.3481 | 0.7246 / 0.6182 / 0.4990 / 0.3560 | 1.092230 | +32.8660 | +7.3740 | +0.000355 / -0.000357 / -0.000365 |
| ま | Noto / Source Han JP Regular | 1000 | 0.6840 | 0.8400 | 0.5240 | 0.3740 | 0.4414 / 0.6787 / 0.4658 / 0.3501 | 0.5498 / 0.7598 / 0.4946 / 0.3623 | 1.146067 | +27.2880 | +9.7380 | +0.000410 / -0.000281 / +0.000256 |
| み | Noto / Source Han JP Regular | 1000 | 0.8760 | 0.8110 | 0.5100 | 0.3455 | 0.4541 / 0.5166 / 0.4683 / 0.3501 | 0.7910 / 0.6641 / 0.4893 / 0.3477 | 1.239516 | +21.8700 | -6.8540 | +0.000262 / +0.000127 / -0.000143 |
| む | Noto / Source Han JP Regular | 1000 | 0.8300 | 0.8350 | 0.5070 | 0.3755 | 0.4844 / 0.5859 / 0.4658 / 0.3447 | 0.5586 / 0.7100 / 0.4863 / 0.3599 | 1.068027 | +19.0840 | +7.7560 | -0.000508 / -0.000082 / -0.000250 |
| め | Noto / Source Han JP Regular | 1000 | 0.8200 | 0.8260 | 0.4960 | 0.3690 | 0.5928 / 0.4990 / 0.4683 / 0.3501 | 0.6611 / 0.6631 / 0.4819 / 0.3599 | 0.984943 | +16.7020 | +10.1780 | +0.000574 / -0.000197 / +0.000314 |
| も | Noto / Source Han JP Regular | 1000 | 0.7760 | 0.8380 | 0.4820 | 0.3730 | 0.4990 / 0.6055 / 0.4692 / 0.3486 | 0.5371 / 0.7227 / 0.4756 / 0.3604 | 1.085869 | +8.0340 | +8.9760 | +0.000922 / -0.000033 / -0.000465 |
| や | Noto / Source Han JP Regular | 1000 | 0.8530 | 0.8590 | 0.4865 | 0.3775 | 0.5430 / 0.6611 / 0.4756 / 0.3491 | 0.6875 / 0.7607 / 0.4814 / 0.3638 | 1.151094 | +12.5880 | +10.0300 | +0.000676 / +0.000402 / +0.000459 |
| ゆ | Noto / Source Han JP Regular | 1000 | 0.7750 | 0.8570 | 0.5195 | 0.3645 | 0.4756 / 0.6357 / 0.4692 / 0.3501 | 0.6357 / 0.7471 / 0.4946 / 0.3569 | 1.129014 | +26.2340 | +3.8740 | +0.000699 / +0.000260 / -0.000365 |
| よ | Noto / Source Han JP Regular | 1000 | 0.7290 | 0.8310 | 0.4905 | 0.3695 | 0.4619 / 0.5420 / 0.4644 / 0.3462 | 0.6367 / 0.6855 / 0.4775 / 0.3574 | 1.063839 | +10.3860 | +4.9340 | -0.000949 / +0.000111 / -0.000424 |
| ら | Noto / Source Han JP Regular | 1000 | 0.6740 | 0.8238 | 0.5150 | 0.3721 | 0.4033 / 0.6172 / 0.4702 / 0.3516 | 0.5693 / 0.7207 / 0.4927 / 0.3613 | 1.086490 | +24.9300 | +8.5033 | +0.000186 / +0.000068 / -0.000492 |
| り | Noto / Source Han JP Regular | 1000 | 0.5800 | 0.8420 | 0.5020 | 0.3710 | 0.2969 / 0.6641 / 0.4697 / 0.3525 | 0.4102 / 0.7529 / 0.4863 / 0.3618 | 1.138791 | +19.5240 | +8.9520 | -0.000102 / +0.000465 / +0.000047 |
| る | Noto / Source Han JP Regular | 1000 | 0.7440 | 0.7970 | 0.4840 | 0.3555 | 0.3994 / 0.5586 / 0.4683 / 0.3467 | 0.4932 / 0.6787 / 0.4761 / 0.3511 | 1.009113 | +12.0580 | -1.4840 | +0.000914 / -0.000057 / -0.000016 |
| れ | Noto / Source Han JP Regular | 1000 | 0.9200 | 0.8320 | 0.5140 | 0.3780 | 0.5439 / 0.6748 / 0.4663 / 0.3501 | 0.8418 / 0.7539 / 0.4902 / 0.3643 | 1.282132 | +22.9180 | +10.2860 | +0.000504 / +0.000080 / +0.000209 |
| ろ | Noto / Source Han JP Regular | 1000 | 0.7440 | 0.7892 | 0.4800 | 0.3504 | 0.3945 / 0.4893 / 0.4688 / 0.3472 | 0.4844 / 0.6396 / 0.4746 / 0.3481 | 0.972211 | +7.7600 | -4.3511 | +0.000408 / +0.000234 / -0.000634 |
| わ | Noto / Source Han JP Regular | 1000 | 0.8740 | 0.8320 | 0.4920 | 0.3780 | 0.6270 / 0.6191 / 0.4834 / 0.3691 | 0.6777 / 0.7246 / 0.4883 / 0.3740 | 1.111751 | +19.4053 | +21.0360 | -0.000961 / +0.000581 / +0.000453 |
| を | Noto / Source Han JP Regular | 1000 | 0.7870 | 0.8430 | 0.4885 | 0.3765 | 0.3975 / 0.7217 / 0.4683 / 0.3472 | 0.6465 / 0.7832 / 0.4785 / 0.3623 | 1.184940 | +9.8620 | +9.0180 | +0.000863 / +0.000135 / +0.000471 |
| ん | Noto / Source Han JP Regular | 1000 | 0.8710 | 0.8160 | 0.5115 | 0.3700 | 0.6006 / 0.6172 / 0.4683 / 0.3467 | 0.6953 / 0.7158 / 0.4902 / 0.3579 | 1.068027 | +24.1380 | +8.9400 | -0.000773 / +0.000354 / -0.000430 |

[Same-em metric-box proof](../proofs/quanfangwei-hiragana-standard-metrics.png): green reference box/center, blue new glyph/box/center, common gray em cell. No reference glyph outline is displayed.

Reproduce measurements with `measure_hiragana_reference_metrics.py --noto /outside/repo/NotoSansCJKjp-Regular.otf --source-han /outside/repo/SourceHanSansJP-Regular.otf`; run `normalize_hiragana_metrics.py`, rebuild canonically, render proofs, and verify with `verify_hiragana_metrics.py`. Measurement snapshots are reviewed data; the verifier does not regenerate them.
