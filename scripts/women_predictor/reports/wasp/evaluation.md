# WASP-style model evaluation

## chronology

- selected_elo_k: 32.0
- evaluated_matches: 597
- selection_rule: minimum 2023-24 pre-match Brier; locked test unused

### validation_brier_by_k

- 16: 0.2258452299256961
- 24: 0.2209142019291167
- 32: 0.2169476509267048

## reduced_match_gate

- development_matches: 27
- minimum_matches: 50
- enabled: False
- reason: insufficient_development_matches

## japan_audit_2026

### japan_batting

- correction_enabled: False

#### base

- states: 399
- matches: 3
- mae: 15.316514984510953
- rmse: 20.412886986424
- match_macro_mae: 15.223886029387934
- match_macro_rmse: 19.92595193230021

#### corrected

- states: 399
- matches: 3
- mae: 15.316514984510953
- rmse: 20.412886986424
- match_macro_mae: 15.223886029387934
- match_macro_rmse: 19.92595193230021

### japan_bowling

- correction_enabled: False

#### base

- states: 249
- matches: 2
- mae: 12.118425054367501
- rmse: 15.674675831019478
- match_macro_mae: 12.09469603681174
- match_macro_rmse: 14.492391364551317

#### corrected

- states: 249
- matches: 2
- mae: 12.118425054367501
- rmse: 15.674675831019478
- match_macro_mae: 12.09469603681174
- match_macro_rmse: 14.492391364551317

### japan_chasing

- correction_enabled: False

#### base

- states: 241
- matches: 2
- brier: 0.015144971333925276
- log_loss: 0.0906521445061015
- match_macro_brier: 0.015165655485788927
- match_macro_log_loss: 0.09102553443465311
- ece: 0.07446212982340893
- calibration_slope: None
- calibration_intercept: None
- roc_auc: None

##### calibration_curve

- `{"bin": 1, "count": 25, "mean_probability": 0.001926654359721295, "observed_rate": 0.0}`
- `{"bin": 2, "count": 24, "mean_probability": 0.006237295164924846, "observed_rate": 0.0}`
- `{"bin": 3, "count": 24, "mean_probability": 0.010162085301221514, "observed_rate": 0.0}`
- `{"bin": 4, "count": 24, "mean_probability": 0.016701039673430756, "observed_rate": 0.0}`
- `{"bin": 5, "count": 24, "mean_probability": 0.02664169394626983, "observed_rate": 0.0}`
- `{"bin": 6, "count": 24, "mean_probability": 0.054200969069082235, "observed_rate": 0.0}`
- `{"bin": 7, "count": 24, "mean_probability": 0.08329007457781556, "observed_rate": 0.0}`
- `{"bin": 8, "count": 24, "mean_probability": 0.11662703994518453, "observed_rate": 0.0}`
- `{"bin": 9, "count": 24, "mean_probability": 0.1612602513812479, "observed_rate": 0.0}`
- `{"bin": 10, "count": 24, "mean_probability": 0.27059650629284443, "observed_rate": 0.0}`

#### corrected

- states: 241
- matches: 2
- brier: 0.015144971333925276
- log_loss: 0.0906521445061015
- match_macro_brier: 0.015165655485788927
- match_macro_log_loss: 0.09102553443465311
- ece: 0.07446212982340893
- calibration_slope: None
- calibration_intercept: None
- roc_auc: None

##### calibration_curve

- `{"bin": 1, "count": 25, "mean_probability": 0.001926654359721295, "observed_rate": 0.0}`
- `{"bin": 2, "count": 24, "mean_probability": 0.006237295164924846, "observed_rate": 0.0}`
- `{"bin": 3, "count": 24, "mean_probability": 0.010162085301221514, "observed_rate": 0.0}`
- `{"bin": 4, "count": 24, "mean_probability": 0.016701039673430756, "observed_rate": 0.0}`
- `{"bin": 5, "count": 24, "mean_probability": 0.02664169394626983, "observed_rate": 0.0}`
- `{"bin": 6, "count": 24, "mean_probability": 0.054200969069082235, "observed_rate": 0.0}`
- `{"bin": 7, "count": 24, "mean_probability": 0.08329007457781556, "observed_rate": 0.0}`
- `{"bin": 8, "count": 24, "mean_probability": 0.11662703994518453, "observed_rate": 0.0}`
- `{"bin": 9, "count": 24, "mean_probability": 0.1612602513812479, "observed_rate": 0.0}`
- `{"bin": 10, "count": 24, "mean_probability": 0.27059650629284443, "observed_rate": 0.0}`

### japan_defending

- correction_enabled: False

#### base

- states: 400
- matches: 3
- brier: 0.05135272228888284
- log_loss: 0.1639844536806848
- match_macro_brier: 0.05266853723228068
- match_macro_log_loss: 0.16807090173603836
- ece: 0.09509077265372184
- calibration_slope: None
- calibration_intercept: None
- roc_auc: None

##### calibration_curve

- `{"bin": 1, "count": 40, "mean_probability": 6.3515866135308e-06, "observed_rate": 0.0}`
- `{"bin": 2, "count": 40, "mean_probability": 4.767384117657222e-05, "observed_rate": 0.0}`
- `{"bin": 3, "count": 40, "mean_probability": 0.00025717462105627524, "observed_rate": 0.0}`
- `{"bin": 4, "count": 40, "mean_probability": 0.001849258299598497, "observed_rate": 0.0}`
- `{"bin": 5, "count": 40, "mean_probability": 0.0054847953448590465, "observed_rate": 0.0}`
- `{"bin": 6, "count": 40, "mean_probability": 0.0069481240927755285, "observed_rate": 0.0}`
- `{"bin": 7, "count": 40, "mean_probability": 0.019565731282305786, "observed_rate": 0.0}`
- `{"bin": 8, "count": 40, "mean_probability": 0.09068032790587802, "observed_rate": 0.0}`
- `{"bin": 9, "count": 40, "mean_probability": 0.18344902029348983, "observed_rate": 0.0}`
- `{"bin": 10, "count": 40, "mean_probability": 0.6426192692694653, "observed_rate": 0.0}`

#### corrected

- states: 400
- matches: 3
- brier: 0.05135272228888284
- log_loss: 0.1639844536806848
- match_macro_brier: 0.05266853723228068
- match_macro_log_loss: 0.16807090173603836
- ece: 0.09509077265372184
- calibration_slope: None
- calibration_intercept: None
- roc_auc: None

##### calibration_curve

- `{"bin": 1, "count": 40, "mean_probability": 6.3515866135308e-06, "observed_rate": 0.0}`
- `{"bin": 2, "count": 40, "mean_probability": 4.767384117657222e-05, "observed_rate": 0.0}`
- `{"bin": 3, "count": 40, "mean_probability": 0.00025717462105627524, "observed_rate": 0.0}`
- `{"bin": 4, "count": 40, "mean_probability": 0.001849258299598497, "observed_rate": 0.0}`
- `{"bin": 5, "count": 40, "mean_probability": 0.0054847953448590465, "observed_rate": 0.0}`
- `{"bin": 6, "count": 40, "mean_probability": 0.0069481240927755285, "observed_rate": 0.0}`
- `{"bin": 7, "count": 40, "mean_probability": 0.019565731282305786, "observed_rate": 0.0}`
- `{"bin": 8, "count": 40, "mean_probability": 0.09068032790587802, "observed_rate": 0.0}`
- `{"bin": 9, "count": 40, "mean_probability": 0.18344902029348983, "observed_rate": 0.0}`
- `{"bin": 10, "count": 40, "mean_probability": 0.6426192692694653, "observed_rate": 0.0}`

## first_innings

- selected: hgb

### locked_test

- states: 88417
- matches: 685
- mae: 15.98264723795996
- rmse: 22.970731197552325
- match_macro_mae: 16.27641884094087
- match_macro_rmse: 20.857601716833955

### intervals

#### overall

##### p50

- nominal_coverage: 0.5
- coverage: 0.5090876188968185
- mean_width: 26.511920626293286
- interval_score: 50.84355985222352

##### p80

- nominal_coverage: 0.8
- coverage: 0.7990771005575851
- mean_width: 50.23833621480344
- interval_score: 69.97117679983657

#### by_slice

##### legal_over

###### 0

- states: 4577
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.47279877649115143
- mean_width: 51.99883434316422
- interval_score: 106.8881022829852

###### p80

- nominal_coverage: 0.8
- coverage: 0.7734323792877431
- mean_width: 102.4385681819378
- interval_score: 147.36446082821098

###### 1

- states: 4571
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.49989061474513236
- mean_width: 49.196669931659706
- interval_score: 97.83565104624495

###### p80

- nominal_coverage: 0.8
- coverage: 0.7700721942682126
- mean_width: 93.9219102343916
- interval_score: 138.20784827828388

###### 10

- states: 4510
- matches: 682

###### p50

- nominal_coverage: 0.5
- coverage: 0.5144124168514412
- mean_width: 24.48268523462253
- interval_score: 44.37523165175304

###### p80

- nominal_coverage: 0.8
- coverage: 0.7955654101995565
- mean_width: 44.44340078161429
- interval_score: 61.94335856803514

###### 11

- states: 4477
- matches: 681

###### p50

- nominal_coverage: 0.5
- coverage: 0.5101630556176011
- mean_width: 22.22549445057791
- interval_score: 40.30865698060512

###### p80

- nominal_coverage: 0.8
- coverage: 0.8058968058968059
- mean_width: 40.63963647779183
- interval_score: 55.701357627219394

###### 12

- states: 4426
- matches: 679

###### p50

- nominal_coverage: 0.5
- coverage: 0.49932218707636694
- mean_width: 19.684047249440063
- interval_score: 36.29255290959269

###### p80

- nominal_coverage: 0.8
- coverage: 0.807049254405784
- mean_width: 36.628651250964005
- interval_score: 49.64532452063429

###### 13

- states: 4416
- matches: 674

###### p50

- nominal_coverage: 0.5
- coverage: 0.5047554347826086
- mean_width: 17.95310169245012
- interval_score: 32.75109465585294

###### p80

- nominal_coverage: 0.8
- coverage: 0.8249547101449275
- mean_width: 34.05970371219737
- interval_score: 44.7751166364774

###### 14

- states: 4342
- matches: 668

###### p50

- nominal_coverage: 0.5
- coverage: 0.5246430216490097
- mean_width: 16.516490347959795
- interval_score: 29.503629544089616

###### p80

- nominal_coverage: 0.8
- coverage: 0.8141409488714878
- mean_width: 30.597165850895454
- interval_score: 40.45839410065759

###### 15

- states: 4256
- matches: 660

###### p50

- nominal_coverage: 0.5
- coverage: 0.5082236842105263
- mean_width: 13.903017972719844
- interval_score: 25.952500249944112

###### p80

- nominal_coverage: 0.8
- coverage: 0.7974624060150376
- mean_width: 26.042719388649754
- interval_score: 36.34253727935347

###### 16

- states: 4257
- matches: 652

###### p50

- nominal_coverage: 0.5
- coverage: 0.551092318534179
- mean_width: 12.278865041083767
- interval_score: 21.652151258119634

###### p80

- nominal_coverage: 0.8
- coverage: 0.8205308902983321
- mean_width: 22.583987628689254
- interval_score: 30.341442927411666

###### 17

- states: 4172
- matches: 643

###### p50

- nominal_coverage: 0.5
- coverage: 0.5711888782358581
- mean_width: 10.366966415146702
- interval_score: 17.610914485494277

###### p80

- nominal_coverage: 0.8
- coverage: 0.8267018216682647
- mean_width: 18.698857121862012
- interval_score: 24.71602957572684

###### 18

- states: 4069
- matches: 631

###### p50

- nominal_coverage: 0.5
- coverage: 0.5394445809781273
- mean_width: 7.811239636649153
- interval_score: 13.862976639092835

###### p80

- nominal_coverage: 0.8
- coverage: 0.805111821086262
- mean_width: 13.851632502123346
- interval_score: 19.29564270034897

###### 19

- states: 3951
- matches: 619

###### p50

- nominal_coverage: 0.5
- coverage: 0.5828904074917742
- mean_width: 4.48017736701479
- interval_score: 7.446236019513114

###### p80

- nominal_coverage: 0.8
- coverage: 0.8683877499367249
- mean_width: 8.198187507953733
- interval_score: 10.316332368720131

###### 2

- states: 4473
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.4846858931365974
- mean_width: 44.51725846218585
- interval_score: 89.3484508955795

###### p80

- nominal_coverage: 0.8
- coverage: 0.7672702883970489
- mean_width: 85.58545178450044
- interval_score: 125.39013945855642

###### 20

- states: 581
- matches: 581

###### p50

- nominal_coverage: 0.5
- coverage: 1.0
- mean_width: 0.0
- interval_score: 0.0

###### p80

- nominal_coverage: 0.8
- coverage: 1.0
- mean_width: 0.0
- interval_score: 0.0

###### 3

- states: 4441
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.4683629813105156
- mean_width: 41.26884337372448
- interval_score: 82.06787265883116

###### p80

- nominal_coverage: 0.8
- coverage: 0.7725737446521054
- mean_width: 79.1183892593448
- interval_score: 110.90588314014688

###### 4

- states: 4506
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.47003994673768307
- mean_width: 38.30037077615331
- interval_score: 75.29461425982572

###### p80

- nominal_coverage: 0.8
- coverage: 0.7758544163337772
- mean_width: 72.70187669820194
- interval_score: 100.5163748104516

###### 5

- states: 4516
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.46811337466784764
- mean_width: 34.9754582417144
- interval_score: 68.2455331015771

###### p80

- nominal_coverage: 0.8
- coverage: 0.7632860938883969
- mean_width: 66.0368187064959
- interval_score: 91.79192788241254

###### 6

- states: 4447
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.48639532268945357
- mean_width: 32.46858586933948
- interval_score: 60.526167376916554

###### p80

- nominal_coverage: 0.8
- coverage: 0.7908702496064762
- mean_width: 60.733139450351274
- interval_score: 81.58042008608948

###### 7

- states: 4466
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.49664128974473803
- mean_width: 29.842524170220845
- interval_score: 55.76365220051964

###### p80

- nominal_coverage: 0.8
- coverage: 0.7987012987012987
- mean_width: 56.98454180073392
- interval_score: 76.55850992494153

###### 8

- states: 4481
- matches: 684

###### p50

- nominal_coverage: 0.5
- coverage: 0.4898460165141709
- mean_width: 27.33884384806607
- interval_score: 52.320781235999256

###### p80

- nominal_coverage: 0.8
- coverage: 0.8013836197277393
- mean_width: 53.057023342388355
- interval_score: 71.75826859869828

###### 9

- states: 4482
- matches: 683

###### p50

- nominal_coverage: 0.5
- coverage: 0.49419901829540386
- mean_width: 25.86137587034006
- interval_score: 48.83341511718482

###### p80

- nominal_coverage: 0.8
- coverage: 0.7900490852298081
- mean_width: 49.06565318478058
- interval_score: 68.09536157904071

##### phase_absolute

###### death

- states: 17030
- matches: 652

###### p50

- nominal_coverage: 0.5
- coverage: 0.5759248385202583
- mean_width: 8.51481075880719
- interval_score: 14.766557463115822

###### p80

- nominal_coverage: 0.8
- coverage: 0.8355842630651791
- mean_width: 15.437756825766504
- interval_score: 20.643135482587027

###### middle

- states: 44303
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.5027876216057603
- mean_width: 23.09751811582084
- interval_score: 42.79469900684563

###### p80

- nominal_coverage: 0.8
- coverage: 0.8025641604406022
- mean_width: 43.35675177522707
- interval_score: 58.867152971933066

###### powerplay

- states: 27084
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.4773667109732683
- mean_width: 43.413377407594005
- interval_score: 86.69424781261638

###### p80

- nominal_coverage: 0.8
- coverage: 0.770417958942549
- mean_width: 83.3770418130109
- interval_score: 119.15143493306536

##### phase_relative

###### death

- states: 17030
- matches: 652

###### p50

- nominal_coverage: 0.5
- coverage: 0.5759248385202583
- mean_width: 8.51481075880719
- interval_score: 14.766557463115822

###### p80

- nominal_coverage: 0.8
- coverage: 0.8355842630651791
- mean_width: 15.437756825766504
- interval_score: 20.643135482587027

###### middle

- states: 44303
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.5027876216057603
- mean_width: 23.09751811582084
- interval_score: 42.79469900684563

###### p80

- nominal_coverage: 0.8
- coverage: 0.8025641604406022
- mean_width: 43.35675177522707
- interval_score: 58.867152971933066

###### powerplay

- states: 27084
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.4773667109732683
- mean_width: 43.413377407594005
- interval_score: 86.69424781261638

###### p80

- nominal_coverage: 0.8
- coverage: 0.770417958942549
- mean_width: 83.3770418130109
- interval_score: 119.15143493306536

##### japan_role

###### japan_batting

- states: 1313
- matches: 10

###### p50

- nominal_coverage: 0.5
- coverage: 0.555978674790556
- mean_width: 27.124155216962002
- interval_score: 41.19023556490175

###### p80

- nominal_coverage: 0.8
- coverage: 0.8918507235338918
- mean_width: 51.371723146886474
- interval_score: 56.57630563154215

###### japan_bowling

- states: 504
- matches: 4

###### p50

- nominal_coverage: 0.5
- coverage: 0.501984126984127
- mean_width: 24.698245629449207
- interval_score: 40.966348310582276

###### p80

- nominal_coverage: 0.8
- coverage: 0.875
- mean_width: 46.88864125349852
- interval_score: 54.92886639026316

###### other

- states: 86600
- matches: 671

###### p50

- nominal_coverage: 0.5
- coverage: 0.508418013856813
- mean_width: 26.513193469028405
- interval_score: 51.047404302642

###### p80

- nominal_coverage: 0.8
- coverage: 0.7972286374133949
- mean_width: 50.24064694481121
- interval_score: 70.26180948217372

##### match_format

###### full

- states: 88417
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.5090876188968185
- mean_width: 26.511920626293286
- interval_score: 50.84355985222352

###### p80

- nominal_coverage: 0.8
- coverage: 0.7990771005575851
- mean_width: 50.23833621480344
- interval_score: 69.97117679983657

### by_slice

#### legal_over

##### 0

- states: 4577
- matches: 685
- mae: 33.19802555999492
- rmse: 41.79589865906517
- match_macro_mae: 32.83379175087569
- match_macro_rmse: 34.00216337161456

##### 1

- states: 4571
- matches: 685
- mae: 30.238235651301466
- rmse: 38.515338157583265
- match_macro_mae: 29.854500391456657
- match_macro_rmse: 30.897402080427828

##### 10

- states: 4510
- matches: 682
- mae: 13.968254859963379
- rmse: 17.75719473228847
- match_macro_mae: 13.961535752791992
- match_macro_rmse: 14.29971729014384

##### 11

- states: 4477
- matches: 681
- mae: 12.747146311066354
- rmse: 16.082405144948478
- match_macro_mae: 12.709228469149911
- match_macro_rmse: 13.02860616670169

##### 12

- states: 4426
- matches: 679
- mae: 11.48618920201933
- rmse: 14.491756590767535
- match_macro_mae: 11.484676219965026
- match_macro_rmse: 11.771613974704534

##### 13

- states: 4416
- matches: 674
- mae: 10.301133919112942
- rmse: 13.013155570858439
- match_macro_mae: 10.306222398086094
- match_macro_rmse: 10.559666690898917

##### 14

- states: 4342
- matches: 668
- mae: 9.164974352920673
- rmse: 11.669685583162556
- match_macro_mae: 9.1395209003852
- match_macro_rmse: 9.406701907782443

##### 15

- states: 4256
- matches: 660
- mae: 8.091290195248318
- rmse: 10.352389904646023
- match_macro_mae: 7.996001512265466
- match_macro_rmse: 8.236568433073527

##### 16

- states: 4257
- matches: 652
- mae: 6.684960814870737
- rmse: 8.609129448361013
- match_macro_mae: 6.690345870390438
- match_macro_rmse: 6.934233679266055

##### 17

- states: 4172
- matches: 643
- mae: 5.445788387679216
- rmse: 7.039883485728678
- match_macro_mae: 5.473177491242251
- match_macro_rmse: 5.725891178804882

##### 18

- states: 4069
- matches: 631
- mae: 4.31174991761907
- rmse: 5.597724109873522
- match_macro_mae: 4.271560168423063
- match_macro_rmse: 4.529961231950051

##### 19

- states: 3951
- matches: 619
- mae: 2.33644143095616
- rmse: 3.1322073832550146
- match_macro_mae: 2.3078168466971785
- match_macro_rmse: 2.6363431775429227

##### 2

- states: 4473
- matches: 685
- mae: 27.89562821607813
- rmse: 35.080794381790156
- match_macro_mae: 27.823850720194525
- match_macro_rmse: 28.658846460157804

##### 20

- states: 581
- matches: 581
- mae: 0.0
- rmse: 0.0
- match_macro_mae: 0.0
- match_macro_rmse: 0.0

##### 3

- states: 4441
- matches: 685
- mae: 26.042348256211586
- rmse: 32.07943050033726
- match_macro_mae: 26.00886990728521
- match_macro_rmse: 26.735167188602915

##### 4

- states: 4506
- matches: 685
- mae: 24.40019749698852
- rmse: 30.578470636497947
- match_macro_mae: 24.1511782583662
- match_macro_rmse: 24.78710767673934

##### 5

- states: 4516
- matches: 685
- mae: 21.83496037759207
- rmse: 27.048765715244105
- match_macro_mae: 21.671852764633467
- match_macro_rmse: 22.201613531669942

##### 6

- states: 4447
- matches: 685
- mae: 19.16681003701385
- rmse: 23.835580437767863
- match_macro_mae: 19.173797259966168
- match_macro_rmse: 19.603905151718124

##### 7

- states: 4466
- matches: 685
- mae: 17.572187939457955
- rmse: 22.002411643611175
- match_macro_mae: 17.52088258495027
- match_macro_rmse: 17.925795701460746

##### 8

- states: 4481
- matches: 684
- mae: 16.34200036521146
- rmse: 20.664746108886142
- match_macro_mae: 16.313806576421754
- match_macro_rmse: 16.687985317358

##### 9

- states: 4482
- matches: 683
- mae: 15.276141692683753
- rmse: 19.416053363563215
- match_macro_mae: 15.123328348221136
- match_macro_rmse: 15.466303354118585

#### phase_absolute

##### death

- states: 17030
- matches: 652
- mae: 4.577422069923793
- rmse: 6.3585517292697915
- match_macro_mae: 4.622262501343993
- match_macro_rmse: 5.449811375804268

##### middle

- states: 44303
- matches: 685
- mae: 13.453551683513952
- rmse: 17.51847849146925
- match_macro_mae: 13.443966931604697
- match_macro_rmse: 15.287900020862025

##### powerplay

- states: 27084
- matches: 685
- mae: 27.291076752074467
- rmse: 34.57050360410424
- match_macro_mae: 27.13957812561087
- match_macro_rmse: 30.017116048510346

#### phase_relative

##### death

- states: 17030
- matches: 652
- mae: 4.577422069923793
- rmse: 6.3585517292697915
- match_macro_mae: 4.622262501343993
- match_macro_rmse: 5.449811375804268

##### middle

- states: 44303
- matches: 685
- mae: 13.453551683513952
- rmse: 17.51847849146925
- match_macro_mae: 13.443966931604697
- match_macro_rmse: 15.287900020862025

##### powerplay

- states: 27084
- matches: 685
- mae: 27.291076752074467
- rmse: 34.57050360410424
- match_macro_mae: 27.13957812561087
- match_macro_rmse: 30.017116048510346

#### japan_role

##### japan_batting

- states: 1313
- matches: 10
- mae: 13.466397696924526
- rmse: 18.404417962909353
- match_macro_mae: 13.361401906468132
- match_macro_rmse: 17.154430827069184

##### japan_bowling

- states: 504
- matches: 4
- mae: 13.520913409224757
- rmse: 17.75973556185074
- match_macro_mae: 13.488948511901057
- match_macro_rmse: 17.034786191152627

##### other

- states: 86600
- matches: 671
- mae: 16.035124714831344
- rmse: 23.059797426373166
- match_macro_mae: 16.336478528960075
- match_macro_rmse: 20.935579318920947

#### match_format

##### full

- states: 88417
- matches: 685
- mae: 15.98264723795996
- rmse: 22.970731197552325
- match_macro_mae: 16.27641884094087
- match_macro_rmse: 20.857601716833955

### selection_model_0

- selected: hgb
- feature_set: model_0
- selection_rule: rolling-origin match-macro MAE with 1% simplicity rule
- model_1_gate_passed: True

#### candidates

- `{"match_macro_mae": 20.381049567559916, "match_macro_rmse": 30.716456029330914, "name": "current_run_rate", "phase_mae": {"death": 4.971436242278065, "middle": 14.860770449016323, "powerplay": 39.05477845488611}}`
- `{"match_macro_mae": 19.98128234497978, "match_macro_rmse": 23.151230835854495, "name": "resource_12", "phase_mae": {"death": 8.896933959765317, "middle": 17.886189738104733, "powerplay": 29.493579802219067}}`
- `{"match_macro_mae": 21.39814861183874, "match_macro_rmse": 24.39345574152069, "name": "resource_24", "phase_mae": {"death": 13.49161188344688, "middle": 18.896907605101894, "powerplay": 29.52664213163276}}`
- `{"match_macro_mae": 23.295359754897223, "match_macro_rmse": 26.34953263353376, "name": "resource_48", "phase_mae": {"death": 20.272901161777124, "middle": 20.066367479755158, "powerplay": 29.563338461647575}}`
- `{"match_macro_mae": 25.430942184898438, "match_macro_rmse": 28.852230971161937, "name": "resource_96", "phase_mae": {"death": 28.02272072097146, "middle": 21.223062046700065, "powerplay": 29.891406305423878}}`
- `{"match_macro_mae": 17.063223980473005, "match_macro_rmse": 20.96969743553643, "name": "ridge", "phase_mae": {"death": 7.278174461188739, "middle": 13.990392997421361, "powerplay": 27.37471371660404}}`
- `{"match_macro_mae": 18.45067429750965, "match_macro_rmse": 23.1231708012982, "name": "tweedie_1.1", "phase_mae": {"death": 10.339515879261127, "middle": 15.040699157301887, "powerplay": 28.567938214088826}}`
- `{"match_macro_mae": 18.715014731158075, "match_macro_rmse": 24.293077172153698, "name": "tweedie_1.5", "phase_mae": {"death": 9.463398185080525, "middle": 15.34079442060035, "powerplay": 29.54832958174303}}`
- `{"match_macro_mae": 15.732000447262108, "match_macro_rmse": 20.099638303199477, "name": "hgb", "phase_mae": {"death": 4.630892746934238, "middle": 13.264339306663402, "powerplay": 26.13081101096511}}`

### selection_model_1

- selected: ridge
- feature_set: model_1
- selection_rule: Model 1 must improve MAE and avoid >5% phase degradation
- model_1_gate_passed: False

#### candidates

- `{"match_macro_mae": 20.381049567559916, "match_macro_rmse": 30.716456029330914, "name": "current_run_rate", "phase_mae": {"death": 4.971436242278065, "middle": 14.860770449016323, "powerplay": 39.05477845488611}}`
- `{"match_macro_mae": 19.98128234497978, "match_macro_rmse": 23.151230835854495, "name": "resource_12", "phase_mae": {"death": 8.896933959765317, "middle": 17.886189738104733, "powerplay": 29.493579802219067}}`
- `{"match_macro_mae": 21.39814861183874, "match_macro_rmse": 24.39345574152069, "name": "resource_24", "phase_mae": {"death": 13.49161188344688, "middle": 18.896907605101894, "powerplay": 29.52664213163276}}`
- `{"match_macro_mae": 23.295359754897223, "match_macro_rmse": 26.34953263353376, "name": "resource_48", "phase_mae": {"death": 20.272901161777124, "middle": 20.066367479755158, "powerplay": 29.563338461647575}}`
- `{"match_macro_mae": 25.430942184898438, "match_macro_rmse": 28.852230971161937, "name": "resource_96", "phase_mae": {"death": 28.02272072097146, "middle": 21.223062046700065, "powerplay": 29.891406305423878}}`
- `{"match_macro_mae": 16.79771716820301, "match_macro_rmse": 20.396693259567915, "name": "ridge", "phase_mae": {"death": 7.3777076759439915, "middle": 14.233399908926927, "powerplay": 26.295126772441115}}`
- `{"match_macro_mae": 17.890249519050546, "match_macro_rmse": 22.098080297128792, "name": "tweedie_1.1", "phase_mae": {"death": 9.819396804668138, "middle": 15.25632571474024, "powerplay": 27.00200910519561}}`
- `{"match_macro_mae": 18.095070354621825, "match_macro_rmse": 23.033603412123533, "name": "tweedie_1.5", "phase_mae": {"death": 9.041980547887999, "middle": 15.512559585631568, "powerplay": 27.78145955860379}}`
- `{"match_macro_mae": 18.18546287660664, "match_macro_rmse": 22.613491600184236, "name": "hgb", "phase_mae": {"death": 4.701003168370263, "middle": 15.372510008367911, "powerplay": 31.627300002284045}}`

## chase

- selected: logistic

### locked_test

- states: 73842
- matches: 681
- brier: 0.10154862540238965
- log_loss: 0.31370192141539577
- match_macro_brier: 0.09085837371853005
- match_macro_log_loss: 0.2833644483184664
- ece: 0.02654830066070857
- calibration_slope: 1.0461166804247797
- calibration_intercept: -0.24539372763082376
- roc_auc: 0.9363876073529155

#### calibration_curve

- `{"bin": 1, "count": 7385, "mean_probability": 0.0005716512984838079, "observed_rate": 0.0}`
- `{"bin": 2, "count": 7385, "mean_probability": 0.00793727265029207, "observed_rate": 0.00040622884224779957}`
- `{"bin": 3, "count": 7384, "mean_probability": 0.03487583251987209, "observed_rate": 0.01868905742145179}`
- `{"bin": 4, "count": 7384, "mean_probability": 0.11204821709262969, "observed_rate": 0.10197724810400867}`
- `{"bin": 5, "count": 7384, "mean_probability": 0.251471166663629, "observed_rate": 0.22467497291440952}`
- `{"bin": 6, "count": 7384, "mean_probability": 0.4433917813023964, "observed_rate": 0.38068797399783316}`
- `{"bin": 7, "count": 7384, "mean_probability": 0.645679442014533, "observed_rate": 0.5689328277356447}`
- `{"bin": 8, "count": 7384, "mean_probability": 0.8147161718037846, "observed_rate": 0.7608342361863488}`
- `{"bin": 9, "count": 7384, "mean_probability": 0.9278179103896294, "observed_rate": 0.9295774647887324}`
- `{"bin": 10, "count": 7384, "mean_probability": 0.98601946617158, "observed_rate": 0.9952600216684724}`

### terminal_inclusive

- states: 74524
- matches: 681
- brier: 0.10061931185878292
- log_loss: 0.31083111431426114
- match_macro_brier: 0.090104478482266
- match_macro_log_loss: 0.2809805217873059
- ece: 0.026328527305327833
- calibration_slope: 1.0461435724136712
- calibration_intercept: -0.24544711943129965
- roc_auc: 0.9375774704542744

#### calibration_curve

- `{"bin": 1, "count": 7453, "mean_probability": 0.000481457277686606, "observed_rate": 0.0}`
- `{"bin": 2, "count": 7453, "mean_probability": 0.007468777134665304, "observed_rate": 0.0001341741580571582}`
- `{"bin": 3, "count": 7453, "mean_probability": 0.033687923173110854, "observed_rate": 0.017710988863544882}`
- `{"bin": 4, "count": 7453, "mean_probability": 0.11024246436700157, "observed_rate": 0.10049644438481148}`
- `{"bin": 5, "count": 7452, "mean_probability": 0.250153286830186, "observed_rate": 0.22289318303811056}`
- `{"bin": 6, "count": 7452, "mean_probability": 0.4436321543392689, "observed_rate": 0.38097155126140636}`
- `{"bin": 7, "count": 7452, "mean_probability": 0.6476774541096322, "observed_rate": 0.5709876543209876}`
- `{"bin": 8, "count": 7452, "mean_probability": 0.817427648502636, "observed_rate": 0.7652979066022544}`
- `{"bin": 9, "count": 7452, "mean_probability": 0.9302160719396142, "observed_rate": 0.9323671497584541}`
- `{"bin": 10, "count": 7452, "mean_probability": 0.9872438634832074, "observed_rate": 0.9961084272678475}`

### by_slice

#### legal_over

##### 0

- states: 4503
- matches: 681
- brier: 0.15724194279981318
- log_loss: 0.47956071780709086
- match_macro_brier: 0.15728830971463076
- match_macro_log_loss: 0.47845521669492336
- ece: 0.07139193292733532
- calibration_slope: 0.6467399554328345
- calibration_intercept: -0.061442126627096985
- roc_auc: 0.8632127210387632

###### calibration_curve

- `{"bin": 1, "count": 451, "mean_probability": 0.003980618956681263, "observed_rate": 0.0022172949002217295}`
- `{"bin": 2, "count": 451, "mean_probability": 0.026745100472907592, "observed_rate": 0.08869179600886919}`
- `{"bin": 3, "count": 451, "mean_probability": 0.08201309339651523, "observed_rate": 0.2328159645232816}`
- `{"bin": 4, "count": 450, "mean_probability": 0.1914662970965061, "observed_rate": 0.2311111111111111}`
- `{"bin": 5, "count": 450, "mean_probability": 0.3415158049488943, "observed_rate": 0.4177777777777778}`
- `{"bin": 6, "count": 450, "mean_probability": 0.5248449581867106, "observed_rate": 0.4866666666666667}`
- `{"bin": 7, "count": 450, "mean_probability": 0.7126505957678994, "observed_rate": 0.5888888888888889}`
- `{"bin": 8, "count": 450, "mean_probability": 0.8539012928990711, "observed_rate": 0.7088888888888889}`
- `{"bin": 9, "count": 450, "mean_probability": 0.9486771487906045, "observed_rate": 0.8866666666666667}`
- `{"bin": 10, "count": 450, "mean_probability": 0.9923137958620868, "observed_rate": 0.9777777777777777}`

##### 1

- states: 4518
- matches: 680
- brier: 0.13845708410041838
- log_loss: 0.41563678333562554
- match_macro_brier: 0.13947685541841034
- match_macro_log_loss: 0.41850270122180816
- ece: 0.05614309006207722
- calibration_slope: 0.7893039026549807
- calibration_intercept: -0.16890402726692547
- roc_auc: 0.8917101067309374

###### calibration_curve

- `{"bin": 1, "count": 452, "mean_probability": 0.0046009772191946035, "observed_rate": 0.0}`
- `{"bin": 2, "count": 452, "mean_probability": 0.029850876978243103, "observed_rate": 0.030973451327433628}`
- `{"bin": 3, "count": 452, "mean_probability": 0.09267508001416842, "observed_rate": 0.17699115044247787}`
- `{"bin": 4, "count": 452, "mean_probability": 0.21613747357915192, "observed_rate": 0.2920353982300885}`
- `{"bin": 5, "count": 452, "mean_probability": 0.3795020180462285, "observed_rate": 0.32079646017699115}`
- `{"bin": 6, "count": 452, "mean_probability": 0.5743282889347844, "observed_rate": 0.48451327433628316}`
- `{"bin": 7, "count": 452, "mean_probability": 0.7375848314628266, "observed_rate": 0.6637168141592921}`
- `{"bin": 8, "count": 452, "mean_probability": 0.8726268164622963, "observed_rate": 0.7278761061946902}`
- `{"bin": 9, "count": 451, "mean_probability": 0.9555547277337518, "observed_rate": 0.9356984478935698}`
- `{"bin": 10, "count": 451, "mean_probability": 0.9916883281812858, "observed_rate": 1.0}`

##### 10

- states: 3935
- matches: 611
- brier: 0.09171457470866999
- log_loss: 0.2876339546485484
- match_macro_brier: 0.09186899607073887
- match_macro_log_loss: 0.28801984140539477
- ece: 0.03262669961839362
- calibration_slope: 1.2212718318229787
- calibration_intercept: -0.3194452679666984
- roc_auc: 0.9488773062874395

###### calibration_curve

- `{"bin": 1, "count": 394, "mean_probability": 0.0008542235050984433, "observed_rate": 0.0}`
- `{"bin": 2, "count": 394, "mean_probability": 0.008493880489618804, "observed_rate": 0.0}`
- `{"bin": 3, "count": 394, "mean_probability": 0.03623512601958683, "observed_rate": 0.005076142131979695}`
- `{"bin": 4, "count": 394, "mean_probability": 0.11708576446799203, "observed_rate": 0.07106598984771574}`
- `{"bin": 5, "count": 394, "mean_probability": 0.27503981922523874, "observed_rate": 0.17766497461928935}`
- `{"bin": 6, "count": 393, "mean_probability": 0.46544354385127584, "observed_rate": 0.44783715012722647}`
- `{"bin": 7, "count": 393, "mean_probability": 0.6643939508256147, "observed_rate": 0.5699745547073791}`
- `{"bin": 8, "count": 393, "mean_probability": 0.818335675836409, "observed_rate": 0.8269720101781171}`
- `{"bin": 9, "count": 393, "mean_probability": 0.9307307448206458, "observed_rate": 0.9236641221374046}`
- `{"bin": 10, "count": 393, "mean_probability": 0.9854163031074119, "observed_rate": 1.0}`

##### 11

- states: 3845
- matches: 597
- brier: 0.08782729057234717
- log_loss: 0.2755174965887238
- match_macro_brier: 0.08787609705553176
- match_macro_log_loss: 0.2758545011469222
- ece: 0.03890415988595386
- calibration_slope: 1.3147568713465851
- calibration_intercept: -0.3566802268101363
- roc_auc: 0.9535420625779416

###### calibration_curve

- `{"bin": 1, "count": 385, "mean_probability": 0.0006949678159166204, "observed_rate": 0.0}`
- `{"bin": 2, "count": 385, "mean_probability": 0.006916848660581941, "observed_rate": 0.0}`
- `{"bin": 3, "count": 385, "mean_probability": 0.029525587263681076, "observed_rate": 0.0}`
- `{"bin": 4, "count": 385, "mean_probability": 0.10642771313298262, "observed_rate": 0.07012987012987013}`
- `{"bin": 5, "count": 385, "mean_probability": 0.26721368677725915, "observed_rate": 0.15064935064935064}`
- `{"bin": 6, "count": 384, "mean_probability": 0.4660377342865649, "observed_rate": 0.390625}`
- `{"bin": 7, "count": 384, "mean_probability": 0.6255777063422902, "observed_rate": 0.5494791666666666}`
- `{"bin": 8, "count": 384, "mean_probability": 0.8144029284226956, "observed_rate": 0.828125}`
- `{"bin": 9, "count": 384, "mean_probability": 0.9269501482325477, "observed_rate": 0.9453125}`
- `{"bin": 10, "count": 384, "mean_probability": 0.9845419073171526, "observed_rate": 1.0}`

##### 12

- states: 3656
- matches: 580
- brier: 0.08857057193244895
- log_loss: 0.2775278781659798
- match_macro_brier: 0.08721575648318677
- match_macro_log_loss: 0.27309461809737473
- ece: 0.03285572071514402
- calibration_slope: 1.3131496676863055
- calibration_intercept: -0.292867421851404
- roc_auc: 0.9518313738517717

###### calibration_curve

- `{"bin": 1, "count": 366, "mean_probability": 0.0006208971301973503, "observed_rate": 0.0}`
- `{"bin": 2, "count": 366, "mean_probability": 0.006212437071417864, "observed_rate": 0.0}`
- `{"bin": 3, "count": 366, "mean_probability": 0.02432861009477526, "observed_rate": 0.0}`
- `{"bin": 4, "count": 366, "mean_probability": 0.08841706303829851, "observed_rate": 0.04918032786885246}`
- `{"bin": 5, "count": 366, "mean_probability": 0.23185896261475386, "observed_rate": 0.12568306010928962}`
- `{"bin": 6, "count": 366, "mean_probability": 0.427098833706412, "observed_rate": 0.366120218579235}`
- `{"bin": 7, "count": 365, "mean_probability": 0.5922097373144429, "observed_rate": 0.547945205479452}`
- `{"bin": 8, "count": 365, "mean_probability": 0.7793788679285141, "observed_rate": 0.7726027397260274}`
- `{"bin": 9, "count": 365, "mean_probability": 0.9052438295437834, "observed_rate": 0.9232876712328767}`
- `{"bin": 10, "count": 365, "mean_probability": 0.9781912283114376, "observed_rate": 1.0}`

##### 13

- states: 3552
- matches: 553
- brier: 0.08441117858491844
- log_loss: 0.2683770936444547
- match_macro_brier: 0.08300345661202568
- match_macro_log_loss: 0.2634897485519805
- ece: 0.03891076307117986
- calibration_slope: 1.3814301911309268
- calibration_intercept: -0.30942900831248465
- roc_auc: 0.9556980647092892

###### calibration_curve

- `{"bin": 1, "count": 356, "mean_probability": 0.0004519507672196805, "observed_rate": 0.0}`
- `{"bin": 2, "count": 356, "mean_probability": 0.004897110411198106, "observed_rate": 0.0}`
- `{"bin": 3, "count": 355, "mean_probability": 0.021008047208361646, "observed_rate": 0.0}`
- `{"bin": 4, "count": 355, "mean_probability": 0.07604673626156963, "observed_rate": 0.022535211267605635}`
- `{"bin": 5, "count": 355, "mean_probability": 0.1938920467763542, "observed_rate": 0.11267605633802817}`
- `{"bin": 6, "count": 355, "mean_probability": 0.3815683942700118, "observed_rate": 0.22253521126760564}`
- `{"bin": 7, "count": 355, "mean_probability": 0.5645760284418995, "observed_rate": 0.5830985915492958}`
- `{"bin": 8, "count": 355, "mean_probability": 0.7352421541089399, "observed_rate": 0.7295774647887324}`
- `{"bin": 9, "count": 355, "mean_probability": 0.8924632740572176, "observed_rate": 0.9098591549295775}`
- `{"bin": 10, "count": 355, "mean_probability": 0.9723891616210099, "observed_rate": 1.0}`

##### 14

- states: 3329
- matches: 525
- brier: 0.08205817135385594
- log_loss: 0.2606454835253628
- match_macro_brier: 0.08187243588352926
- match_macro_log_loss: 0.2600605971899165
- ece: 0.03369397214812155
- calibration_slope: 1.392033764493916
- calibration_intercept: -0.2801809274667599
- roc_auc: 0.9570315549706826

###### calibration_curve

- `{"bin": 1, "count": 333, "mean_probability": 0.0002974220687888082, "observed_rate": 0.0}`
- `{"bin": 2, "count": 333, "mean_probability": 0.0028141534867756257, "observed_rate": 0.0}`
- `{"bin": 3, "count": 333, "mean_probability": 0.015809550397599178, "observed_rate": 0.0}`
- `{"bin": 4, "count": 333, "mean_probability": 0.05646841618570371, "observed_rate": 0.003003003003003003}`
- `{"bin": 5, "count": 333, "mean_probability": 0.16456490695437126, "observed_rate": 0.08708708708708708}`
- `{"bin": 6, "count": 333, "mean_probability": 0.3300956341063698, "observed_rate": 0.2132132132132132}`
- `{"bin": 7, "count": 333, "mean_probability": 0.5159529195315234, "observed_rate": 0.4954954954954955}`
- `{"bin": 8, "count": 333, "mean_probability": 0.7120800407495202, "observed_rate": 0.7267267267267268}`
- `{"bin": 9, "count": 333, "mean_probability": 0.8723765818629005, "observed_rate": 0.8708708708708709}`
- `{"bin": 10, "count": 332, "mean_probability": 0.96641721331062, "observed_rate": 1.0}`

##### 15

- states: 3080
- matches: 495
- brier: 0.0818012853125018
- log_loss: 0.2581040832082323
- match_macro_brier: 0.08083834607337216
- match_macro_log_loss: 0.25529118274326146
- ece: 0.03416531184754097
- calibration_slope: 1.3303870464596335
- calibration_intercept: -0.24003889977647308
- roc_auc: 0.955742864283348

###### calibration_curve

- `{"bin": 1, "count": 308, "mean_probability": 0.0001918207202977945, "observed_rate": 0.0}`
- `{"bin": 2, "count": 308, "mean_probability": 0.0018917234992264918, "observed_rate": 0.0}`
- `{"bin": 3, "count": 308, "mean_probability": 0.010215953186006954, "observed_rate": 0.0}`
- `{"bin": 4, "count": 308, "mean_probability": 0.04440109428867931, "observed_rate": 0.0}`
- `{"bin": 5, "count": 308, "mean_probability": 0.1323181076593074, "observed_rate": 0.022727272727272728}`
- `{"bin": 6, "count": 308, "mean_probability": 0.27951095731378695, "observed_rate": 0.2435064935064935}`
- `{"bin": 7, "count": 308, "mean_probability": 0.46172065147463043, "observed_rate": 0.4383116883116883}`
- `{"bin": 8, "count": 308, "mean_probability": 0.6765159668944757, "observed_rate": 0.698051948051948}`
- `{"bin": 9, "count": 308, "mean_probability": 0.8539327487466869, "observed_rate": 0.7987012987012987}`
- `{"bin": 10, "count": 308, "mean_probability": 0.9608191663239316, "observed_rate": 1.0}`

##### 16

- states: 2905
- matches: 465
- brier: 0.07959743551856817
- log_loss: 0.25282904179884397
- match_macro_brier: 0.07727178658627624
- match_macro_log_loss: 0.246479412671166
- ece: 0.043654559843307544
- calibration_slope: 1.3237219815053762
- calibration_intercept: -0.1964427169681251
- roc_auc: 0.9563182263297787

###### calibration_curve

- `{"bin": 1, "count": 291, "mean_probability": 9.636649624493504e-05, "observed_rate": 0.0}`
- `{"bin": 2, "count": 291, "mean_probability": 0.000976555290231516, "observed_rate": 0.0}`
- `{"bin": 3, "count": 291, "mean_probability": 0.00716495873248031, "observed_rate": 0.0}`
- `{"bin": 4, "count": 291, "mean_probability": 0.03247266210805066, "observed_rate": 0.0}`
- `{"bin": 5, "count": 291, "mean_probability": 0.10792607398133137, "observed_rate": 0.054982817869415807}`
- `{"bin": 6, "count": 290, "mean_probability": 0.23804174820781765, "observed_rate": 0.10689655172413794}`
- `{"bin": 7, "count": 290, "mean_probability": 0.4177363951274557, "observed_rate": 0.36551724137931035}`
- `{"bin": 8, "count": 290, "mean_probability": 0.6169737081735372, "observed_rate": 0.7}`
- `{"bin": 9, "count": 290, "mean_probability": 0.8261037141914341, "observed_rate": 0.7862068965517242}`
- `{"bin": 10, "count": 290, "mean_probability": 0.9560693875884052, "observed_rate": 0.993103448275862}`

##### 17

- states: 2515
- matches: 415
- brier: 0.07888247492102246
- log_loss: 0.2525341761459901
- match_macro_brier: 0.07544812793105989
- match_macro_log_loss: 0.2424382415013132
- ece: 0.03974667333464096
- calibration_slope: 1.3222729775681608
- calibration_intercept: -0.15331173318917352
- roc_auc: 0.9539213683011707

###### calibration_curve

- `{"bin": 1, "count": 252, "mean_probability": 3.6056720822463284e-05, "observed_rate": 0.0}`
- `{"bin": 2, "count": 252, "mean_probability": 0.0005768182167785707, "observed_rate": 0.0}`
- `{"bin": 3, "count": 252, "mean_probability": 0.005352124751499319, "observed_rate": 0.0}`
- `{"bin": 4, "count": 252, "mean_probability": 0.027222572362858584, "observed_rate": 0.0}`
- `{"bin": 5, "count": 252, "mean_probability": 0.08585538089483534, "observed_rate": 0.047619047619047616}`
- `{"bin": 6, "count": 251, "mean_probability": 0.2010199022114286, "observed_rate": 0.06772908366533864}`
- `{"bin": 7, "count": 251, "mean_probability": 0.3515494577367394, "observed_rate": 0.2788844621513944}`
- `{"bin": 8, "count": 251, "mean_probability": 0.5586580038821962, "observed_rate": 0.6294820717131474}`
- `{"bin": 9, "count": 251, "mean_probability": 0.7732872895155294, "observed_rate": 0.8127490039840638}`
- `{"bin": 10, "count": 251, "mean_probability": 0.9346112294417083, "observed_rate": 0.9243027888446215}`

##### 18

- states: 2136
- matches: 356
- brier: 0.07443080395127029
- log_loss: 0.23334132154020548
- match_macro_brier: 0.07089351668259375
- match_macro_log_loss: 0.22419203539961696
- ece: 0.029871958308417483
- calibration_slope: 1.1561975178066124
- calibration_intercept: -0.18497773924383074
- roc_auc: 0.9524665890452566

###### calibration_curve

- `{"bin": 1, "count": 214, "mean_probability": 3.2330466841307185e-06, "observed_rate": 0.0}`
- `{"bin": 2, "count": 214, "mean_probability": 0.00011737259191438532, "observed_rate": 0.0}`
- `{"bin": 3, "count": 214, "mean_probability": 0.0014934146309887608, "observed_rate": 0.0}`
- `{"bin": 4, "count": 214, "mean_probability": 0.00932243764197177, "observed_rate": 0.0}`
- `{"bin": 5, "count": 214, "mean_probability": 0.038608958352840506, "observed_rate": 0.0}`
- `{"bin": 6, "count": 214, "mean_probability": 0.10515908118333742, "observed_rate": 0.018691588785046728}`
- `{"bin": 7, "count": 213, "mean_probability": 0.22323273773744567, "observed_rate": 0.2676056338028169}`
- `{"bin": 8, "count": 213, "mean_probability": 0.4211830905964866, "observed_rate": 0.3474178403755869}`
- `{"bin": 9, "count": 213, "mean_probability": 0.7020270066353621, "observed_rate": 0.7183098591549296}`
- `{"bin": 10, "count": 213, "mean_probability": 0.911117688954556, "observed_rate": 0.8826291079812206}`

##### 19

- states: 1652
- matches: 289
- brier: 0.04906247561514167
- log_loss: 0.15257180918093358
- match_macro_brier: 0.055848801136221975
- match_macro_log_loss: 0.17293890362103592
- ece: 0.013330812290974249
- calibration_slope: 1.0050104253057117
- calibration_intercept: -0.1768580004808554
- roc_auc: 0.9588585655462989

###### calibration_curve

- `{"bin": 1, "count": 166, "mean_probability": 1e-06, "observed_rate": 0.0}`
- `{"bin": 2, "count": 166, "mean_probability": 1e-06, "observed_rate": 0.0}`
- `{"bin": 3, "count": 165, "mean_probability": 1.2396204508207102e-06, "observed_rate": 0.0}`
- `{"bin": 4, "count": 165, "mean_probability": 3.0793797877250375e-05, "observed_rate": 0.0}`
- `{"bin": 5, "count": 165, "mean_probability": 0.0005031805173847744, "observed_rate": 0.0}`
- `{"bin": 6, "count": 165, "mean_probability": 0.00461776026897989, "observed_rate": 0.0}`
- `{"bin": 7, "count": 165, "mean_probability": 0.02663746347839558, "observed_rate": 0.012121212121212121}`
- `{"bin": 8, "count": 165, "mean_probability": 0.09717777425930138, "observed_rate": 0.08484848484848485}`
- `{"bin": 9, "count": 165, "mean_probability": 0.3104981115480713, "observed_rate": 0.3333333333333333}`
- `{"bin": 10, "count": 165, "mean_probability": 0.721058202058345, "observed_rate": 0.6424242424242425}`

##### 2

- states: 4411
- matches: 679
- brier: 0.1276527141218348
- log_loss: 0.38370875253276493
- match_macro_brier: 0.127792106465827
- match_macro_log_loss: 0.38454670898728127
- ece: 0.04534762904089108
- calibration_slope: 0.874186973571058
- calibration_intercept: -0.22040659168831828
- roc_auc: 0.9067555070200741

###### calibration_curve

- `{"bin": 1, "count": 442, "mean_probability": 0.004177640970386998, "observed_rate": 0.0}`
- `{"bin": 2, "count": 441, "mean_probability": 0.02551746437835984, "observed_rate": 0.006802721088435374}`
- `{"bin": 3, "count": 441, "mean_probability": 0.09474703059151096, "observed_rate": 0.1383219954648526}`
- `{"bin": 4, "count": 441, "mean_probability": 0.21432013857267374, "observed_rate": 0.25396825396825395}`
- `{"bin": 5, "count": 441, "mean_probability": 0.37615081821602714, "observed_rate": 0.35600907029478457}`
- `{"bin": 6, "count": 441, "mean_probability": 0.577379264126854, "observed_rate": 0.4557823129251701}`
- `{"bin": 7, "count": 441, "mean_probability": 0.7551242567604212, "observed_rate": 0.6598639455782312}`
- `{"bin": 8, "count": 441, "mean_probability": 0.8663780858586245, "observed_rate": 0.7777777777777778}`
- `{"bin": 9, "count": 441, "mean_probability": 0.9551315435411051, "observed_rate": 0.9410430839002267}`
- `{"bin": 10, "count": 441, "mean_probability": 0.9922335961651447, "observed_rate": 1.0}`

##### 3

- states: 4402
- matches: 677
- brier: 0.11828739604454144
- log_loss: 0.3598218664620237
- match_macro_brier: 0.11897248038871465
- match_macro_log_loss: 0.3620288435204061
- ece: 0.036478274718159155
- calibration_slope: 0.92482649999461
- calibration_intercept: -0.22501532394782583
- roc_auc: 0.9189181600359408

###### calibration_curve

- `{"bin": 1, "count": 441, "mean_probability": 0.004222852457759862, "observed_rate": 0.0}`
- `{"bin": 2, "count": 441, "mean_probability": 0.023110217729887146, "observed_rate": 0.0022675736961451248}`
- `{"bin": 3, "count": 440, "mean_probability": 0.08382827762814668, "observed_rate": 0.10681818181818181}`
- `{"bin": 4, "count": 440, "mean_probability": 0.19710953574519982, "observed_rate": 0.22045454545454546}`
- `{"bin": 5, "count": 440, "mean_probability": 0.3610220964067126, "observed_rate": 0.35}`
- `{"bin": 6, "count": 440, "mean_probability": 0.5789608588808495, "observed_rate": 0.4590909090909091}`
- `{"bin": 7, "count": 440, "mean_probability": 0.7545680186884786, "observed_rate": 0.6772727272727272}`
- `{"bin": 8, "count": 440, "mean_probability": 0.8743705875789142, "observed_rate": 0.8159090909090909}`
- `{"bin": 9, "count": 440, "mean_probability": 0.9556500036308017, "observed_rate": 0.9363636363636364}`
- `{"bin": 10, "count": 440, "mean_probability": 0.9924440214565367, "observed_rate": 1.0}`

##### 4

- states: 4404
- matches: 670
- brier: 0.11004076948611317
- log_loss: 0.33713908066410475
- match_macro_brier: 0.11207692849362033
- match_macro_log_loss: 0.34274919589504244
- ece: 0.038215706920368395
- calibration_slope: 0.9864401891485801
- calibration_intercept: -0.20769879347141676
- roc_auc: 0.9293886795968395

###### calibration_curve

- `{"bin": 1, "count": 441, "mean_probability": 0.0032107077406732516, "observed_rate": 0.0}`
- `{"bin": 2, "count": 441, "mean_probability": 0.02026902028078271, "observed_rate": 0.0}`
- `{"bin": 3, "count": 441, "mean_probability": 0.07467387420499838, "observed_rate": 0.09977324263038549}`
- `{"bin": 4, "count": 441, "mean_probability": 0.18223643447616278, "observed_rate": 0.1564625850340136}`
- `{"bin": 5, "count": 440, "mean_probability": 0.34166470768554186, "observed_rate": 0.37727272727272726}`
- `{"bin": 6, "count": 440, "mean_probability": 0.5704913576985853, "observed_rate": 0.43863636363636366}`
- `{"bin": 7, "count": 440, "mean_probability": 0.7592584067287416, "observed_rate": 0.6568181818181819}`
- `{"bin": 8, "count": 440, "mean_probability": 0.87460188599839, "observed_rate": 0.8568181818181818}`
- `{"bin": 9, "count": 440, "mean_probability": 0.9516853495166885, "observed_rate": 0.9636363636363636}`
- `{"bin": 10, "count": 440, "mean_probability": 0.99165540199563, "observed_rate": 1.0}`

##### 5

- states: 4372
- matches: 666
- brier: 0.10618659586191737
- log_loss: 0.3249693024765727
- match_macro_brier: 0.10514609728841719
- match_macro_log_loss: 0.3226216520714917
- ece: 0.044121579631345345
- calibration_slope: 1.0595663943270586
- calibration_intercept: -0.3060479972946072
- roc_auc: 0.93502898988134

###### calibration_curve

- `{"bin": 1, "count": 438, "mean_probability": 0.0027572018247622072, "observed_rate": 0.0}`
- `{"bin": 2, "count": 438, "mean_probability": 0.01992099034496002, "observed_rate": 0.0}`
- `{"bin": 3, "count": 437, "mean_probability": 0.07545069662816328, "observed_rate": 0.08466819221967964}`
- `{"bin": 4, "count": 437, "mean_probability": 0.18060834973287387, "observed_rate": 0.15331807780320367}`
- `{"bin": 5, "count": 437, "mean_probability": 0.3559040828065945, "observed_rate": 0.3524027459954233}`
- `{"bin": 6, "count": 437, "mean_probability": 0.5644000794890056, "observed_rate": 0.37757437070938216}`
- `{"bin": 7, "count": 437, "mean_probability": 0.7491918192140461, "observed_rate": 0.6155606407322655}`
- `{"bin": 8, "count": 437, "mean_probability": 0.8709950877773119, "observed_rate": 0.8924485125858124}`
- `{"bin": 9, "count": 437, "mean_probability": 0.950875517654071, "observed_rate": 0.9794050343249427}`
- `{"bin": 10, "count": 437, "mean_probability": 0.9917612946797622, "observed_rate": 1.0}`

##### 6

- states: 4246
- matches: 658
- brier: 0.09996001798139115
- log_loss: 0.308824115967964
- match_macro_brier: 0.10097314340529046
- match_macro_log_loss: 0.3118372557041579
- ece: 0.039126832982305605
- calibration_slope: 1.1060181672893692
- calibration_intercept: -0.32662333646992503
- roc_auc: 0.9423502927539987

###### calibration_curve

- `{"bin": 1, "count": 425, "mean_probability": 0.002425222259714696, "observed_rate": 0.0}`
- `{"bin": 2, "count": 425, "mean_probability": 0.017570208948200324, "observed_rate": 0.0}`
- `{"bin": 3, "count": 425, "mean_probability": 0.0681525548008486, "observed_rate": 0.05411764705882353}`
- `{"bin": 4, "count": 425, "mean_probability": 0.17056478103730147, "observed_rate": 0.14823529411764705}`
- `{"bin": 5, "count": 425, "mean_probability": 0.35350657122322915, "observed_rate": 0.3270588235294118}`
- `{"bin": 6, "count": 425, "mean_probability": 0.5701680938540987, "observed_rate": 0.36470588235294116}`
- `{"bin": 7, "count": 424, "mean_probability": 0.7511579856894165, "observed_rate": 0.7075471698113207}`
- `{"bin": 8, "count": 424, "mean_probability": 0.8795741954738169, "observed_rate": 0.8632075471698113}`
- `{"bin": 9, "count": 424, "mean_probability": 0.9539901001820175, "observed_rate": 0.9882075471698113}`
- `{"bin": 10, "count": 424, "mean_probability": 0.9913225663811509, "observed_rate": 1.0}`

##### 7

- states: 4190
- matches: 648
- brier: 0.09655203388307221
- log_loss: 0.29935150036926805
- match_macro_brier: 0.09628725499216406
- match_macro_log_loss: 0.29923577109978855
- ece: 0.042502354953277074
- calibration_slope: 1.149610036968084
- calibration_intercept: -0.3401580791105354
- roc_auc: 0.9453462268637197

###### calibration_curve

- `{"bin": 1, "count": 419, "mean_probability": 0.0017204550206789582, "observed_rate": 0.0}`
- `{"bin": 2, "count": 419, "mean_probability": 0.01426820764234908, "observed_rate": 0.0}`
- `{"bin": 3, "count": 419, "mean_probability": 0.06004763185767299, "observed_rate": 0.04295942720763723}`
- `{"bin": 4, "count": 419, "mean_probability": 0.14998624245018252, "observed_rate": 0.07875894988066826}`
- `{"bin": 5, "count": 419, "mean_probability": 0.3244295187515354, "observed_rate": 0.3269689737470167}`
- `{"bin": 6, "count": 419, "mean_probability": 0.5400856365098837, "observed_rate": 0.360381861575179}`
- `{"bin": 7, "count": 419, "mean_probability": 0.7278494908043744, "observed_rate": 0.6968973747016707}`
- `{"bin": 8, "count": 419, "mean_probability": 0.865334729665646, "observed_rate": 0.8138424821002387}`
- `{"bin": 9, "count": 419, "mean_probability": 0.9490537723363114, "observed_rate": 0.9952267303102625}`
- `{"bin": 10, "count": 419, "mean_probability": 0.9901411619220556, "observed_rate": 1.0}`

##### 8

- states: 4134
- matches: 639
- brier: 0.09660539420693799
- log_loss: 0.2996296479597562
- match_macro_brier: 0.09487293154253974
- match_macro_log_loss: 0.2953537811716181
- ece: 0.037216550488802534
- calibration_slope: 1.1281058886926663
- calibration_intercept: -0.3339928955021676
- roc_auc: 0.9450685713520729

###### calibration_curve

- `{"bin": 1, "count": 414, "mean_probability": 0.001399489583871082, "observed_rate": 0.0}`
- `{"bin": 2, "count": 414, "mean_probability": 0.011671950756093296, "observed_rate": 0.0}`
- `{"bin": 3, "count": 414, "mean_probability": 0.05021098055624957, "observed_rate": 0.03140096618357488}`
- `{"bin": 4, "count": 414, "mean_probability": 0.14480845178272947, "observed_rate": 0.0966183574879227}`
- `{"bin": 5, "count": 413, "mean_probability": 0.3167214756258501, "observed_rate": 0.3099273607748184}`
- `{"bin": 6, "count": 413, "mean_probability": 0.5353739533529012, "observed_rate": 0.3728813559322034}`
- `{"bin": 7, "count": 413, "mean_probability": 0.7219207896920795, "observed_rate": 0.6682808716707022}`
- `{"bin": 8, "count": 413, "mean_probability": 0.8623305242036414, "observed_rate": 0.8280871670702179}`
- `{"bin": 9, "count": 413, "mean_probability": 0.9495761038907063, "observed_rate": 0.9733656174334141}`
- `{"bin": 10, "count": 413, "mean_probability": 0.9886989720790998, "observed_rate": 1.0}`

##### 9

- states: 4057
- matches: 630
- brier: 0.09537569274918668
- log_loss: 0.2955433378887103
- match_macro_brier: 0.09362086539842772
- match_macro_log_loss: 0.2910260426449293
- ece: 0.03408961572604737
- calibration_slope: 1.1545254115967603
- calibration_intercept: -0.3145358578436987
- roc_auc: 0.9456308740249493

###### calibration_curve

- `{"bin": 1, "count": 406, "mean_probability": 0.0011614181627946968, "observed_rate": 0.0}`
- `{"bin": 2, "count": 406, "mean_probability": 0.010773702598328052, "observed_rate": 0.0}`
- `{"bin": 3, "count": 406, "mean_probability": 0.044997859914711114, "observed_rate": 0.012315270935960592}`
- `{"bin": 4, "count": 406, "mean_probability": 0.13506906078475328, "observed_rate": 0.06896551724137931}`
- `{"bin": 5, "count": 406, "mean_probability": 0.29895825256055686, "observed_rate": 0.27586206896551724}`
- `{"bin": 6, "count": 406, "mean_probability": 0.5004686875316879, "observed_rate": 0.4408866995073892}`
- `{"bin": 7, "count": 406, "mean_probability": 0.7002683169213088, "observed_rate": 0.5812807881773399}`
- `{"bin": 8, "count": 405, "mean_probability": 0.845644090382524, "observed_rate": 0.8518518518518519}`
- `{"bin": 9, "count": 405, "mean_probability": 0.9455116311415237, "observed_rate": 0.9555555555555556}`
- `{"bin": 10, "count": 405, "mean_probability": 0.9879246048461424, "observed_rate": 1.0}`

#### phase_absolute

##### death

- states: 9208
- matches: 465
- brier: 0.0727253889622002
- log_loss: 0.23024082439287444
- match_macro_brier: 0.06347877802198557
- match_macro_log_loss: 0.2061763441396507
- ece: 0.01889082424122498
- calibration_slope: 1.239015231885419
- calibration_intercept: -0.16640304682605753
- roc_auc: 0.9568092250813024

###### calibration_curve

- `{"bin": 1, "count": 921, "mean_probability": 1.4645158782806586e-06, "observed_rate": 0.0}`
- `{"bin": 2, "count": 921, "mean_probability": 0.00012846684592835594, "observed_rate": 0.0}`
- `{"bin": 3, "count": 921, "mean_probability": 0.0014691094910417248, "observed_rate": 0.0}`
- `{"bin": 4, "count": 921, "mean_probability": 0.00941704764918567, "observed_rate": 0.0}`
- `{"bin": 5, "count": 921, "mean_probability": 0.04207549982850674, "observed_rate": 0.0054288816503800215}`
- `{"bin": 6, "count": 921, "mean_probability": 0.12284274511873898, "observed_rate": 0.0749185667752443}`
- `{"bin": 7, "count": 921, "mean_probability": 0.266368196086214, "observed_rate": 0.19109663409337677}`
- `{"bin": 8, "count": 921, "mean_probability": 0.47636286405156586, "observed_rate": 0.46905537459283386}`
- `{"bin": 9, "count": 920, "mean_probability": 0.7306222006928319, "observed_rate": 0.7402173913043478}`
- `{"bin": 10, "count": 920, "mean_probability": 0.9282301013511706, "observed_rate": 0.9293478260869565}`

##### middle

- states: 38024
- matches: 658
- brier: 0.09106469744638751
- log_loss: 0.2846888650718029
- match_macro_brier: 0.082003235634494
- match_macro_log_loss: 0.2582188043369713
- ece: 0.03340135828557336
- calibration_slope: 1.2258488887326489
- calibration_intercept: -0.31673714530653263
- roc_auc: 0.9496002423980577

###### calibration_curve

- `{"bin": 1, "count": 3803, "mean_probability": 0.00073135586381409, "observed_rate": 0.0}`
- `{"bin": 2, "count": 3803, "mean_probability": 0.007722358476273818, "observed_rate": 0.0}`
- `{"bin": 3, "count": 3803, "mean_probability": 0.032508684220465565, "observed_rate": 0.004996055745464107}`
- `{"bin": 4, "count": 3803, "mean_probability": 0.10931313046654198, "observed_rate": 0.059426768340783594}`
- `{"bin": 5, "count": 3802, "mean_probability": 0.25524245558414876, "observed_rate": 0.1954234613361389}`
- `{"bin": 6, "count": 3802, "mean_probability": 0.4525495652837464, "observed_rate": 0.3750657548658601}`
- `{"bin": 7, "count": 3802, "mean_probability": 0.6449593782844758, "observed_rate": 0.5754865860073646}`
- `{"bin": 8, "count": 3802, "mean_probability": 0.8139142972051677, "observed_rate": 0.800894266175697}`
- `{"bin": 9, "count": 3802, "mean_probability": 0.9275669658806996, "observed_rate": 0.9400315623356128}`
- `{"bin": 10, "count": 3802, "mean_probability": 0.984086786615556, "observed_rate": 1.0}`

##### powerplay

- states: 26610
- matches: 681
- brier: 0.12650335060871398
- log_loss: 0.3840402241509145
- match_macro_brier: 0.12600694230156964
- match_macro_log_loss: 0.3827656179118567
- ece: 0.04042273197666212
- calibration_slope: 0.8560289669567481
- calibration_intercept: -0.18133392079188063
- roc_auc: 0.9073970723764202

###### calibration_curve

- `{"bin": 1, "count": 2661, "mean_probability": 0.0037566865129622646, "observed_rate": 0.0003757985719654265}`
- `{"bin": 2, "count": 2661, "mean_probability": 0.023886717695015307, "observed_rate": 0.020293122886133032}`
- `{"bin": 3, "count": 2661, "mean_probability": 0.08362959039749994, "observed_rate": 0.1386696730552424}`
- `{"bin": 4, "count": 2661, "mean_probability": 0.19637931767984082, "observed_rate": 0.22848553175497932}`
- `{"bin": 5, "count": 2661, "mean_probability": 0.3586731646278454, "observed_rate": 0.3543780533633972}`
- `{"bin": 6, "count": 2661, "mean_probability": 0.5646014510742546, "observed_rate": 0.4513340849304773}`
- `{"bin": 7, "count": 2661, "mean_probability": 0.7444573200650936, "observed_rate": 0.6392333709131905}`
- `{"bin": 8, "count": 2661, "mean_probability": 0.8690234708433382, "observed_rate": 0.7985719654265314}`
- `{"bin": 9, "count": 2661, "mean_probability": 0.9529021222022772, "observed_rate": 0.9402480270574972}`
- `{"bin": 10, "count": 2661, "mean_probability": 0.9920275011181999, "observed_rate": 0.9962420142803458}`

#### phase_relative

##### death

- states: 9208
- matches: 465
- brier: 0.0727253889622002
- log_loss: 0.23024082439287444
- match_macro_brier: 0.06347877802198557
- match_macro_log_loss: 0.2061763441396507
- ece: 0.01889082424122498
- calibration_slope: 1.239015231885419
- calibration_intercept: -0.16640304682605753
- roc_auc: 0.9568092250813024

###### calibration_curve

- `{"bin": 1, "count": 921, "mean_probability": 1.4645158782806586e-06, "observed_rate": 0.0}`
- `{"bin": 2, "count": 921, "mean_probability": 0.00012846684592835594, "observed_rate": 0.0}`
- `{"bin": 3, "count": 921, "mean_probability": 0.0014691094910417248, "observed_rate": 0.0}`
- `{"bin": 4, "count": 921, "mean_probability": 0.00941704764918567, "observed_rate": 0.0}`
- `{"bin": 5, "count": 921, "mean_probability": 0.04207549982850674, "observed_rate": 0.0054288816503800215}`
- `{"bin": 6, "count": 921, "mean_probability": 0.12284274511873898, "observed_rate": 0.0749185667752443}`
- `{"bin": 7, "count": 921, "mean_probability": 0.266368196086214, "observed_rate": 0.19109663409337677}`
- `{"bin": 8, "count": 921, "mean_probability": 0.47636286405156586, "observed_rate": 0.46905537459283386}`
- `{"bin": 9, "count": 920, "mean_probability": 0.7306222006928319, "observed_rate": 0.7402173913043478}`
- `{"bin": 10, "count": 920, "mean_probability": 0.9282301013511706, "observed_rate": 0.9293478260869565}`

##### middle

- states: 38024
- matches: 658
- brier: 0.09106469744638751
- log_loss: 0.2846888650718029
- match_macro_brier: 0.082003235634494
- match_macro_log_loss: 0.2582188043369713
- ece: 0.03340135828557336
- calibration_slope: 1.2258488887326489
- calibration_intercept: -0.31673714530653263
- roc_auc: 0.9496002423980577

###### calibration_curve

- `{"bin": 1, "count": 3803, "mean_probability": 0.00073135586381409, "observed_rate": 0.0}`
- `{"bin": 2, "count": 3803, "mean_probability": 0.007722358476273818, "observed_rate": 0.0}`
- `{"bin": 3, "count": 3803, "mean_probability": 0.032508684220465565, "observed_rate": 0.004996055745464107}`
- `{"bin": 4, "count": 3803, "mean_probability": 0.10931313046654198, "observed_rate": 0.059426768340783594}`
- `{"bin": 5, "count": 3802, "mean_probability": 0.25524245558414876, "observed_rate": 0.1954234613361389}`
- `{"bin": 6, "count": 3802, "mean_probability": 0.4525495652837464, "observed_rate": 0.3750657548658601}`
- `{"bin": 7, "count": 3802, "mean_probability": 0.6449593782844758, "observed_rate": 0.5754865860073646}`
- `{"bin": 8, "count": 3802, "mean_probability": 0.8139142972051677, "observed_rate": 0.800894266175697}`
- `{"bin": 9, "count": 3802, "mean_probability": 0.9275669658806996, "observed_rate": 0.9400315623356128}`
- `{"bin": 10, "count": 3802, "mean_probability": 0.984086786615556, "observed_rate": 1.0}`

##### powerplay

- states: 26610
- matches: 681
- brier: 0.12650335060871398
- log_loss: 0.3840402241509145
- match_macro_brier: 0.12600694230156964
- match_macro_log_loss: 0.3827656179118567
- ece: 0.04042273197666212
- calibration_slope: 0.8560289669567481
- calibration_intercept: -0.18133392079188063
- roc_auc: 0.9073970723764202

###### calibration_curve

- `{"bin": 1, "count": 2661, "mean_probability": 0.0037566865129622646, "observed_rate": 0.0003757985719654265}`
- `{"bin": 2, "count": 2661, "mean_probability": 0.023886717695015307, "observed_rate": 0.020293122886133032}`
- `{"bin": 3, "count": 2661, "mean_probability": 0.08362959039749994, "observed_rate": 0.1386696730552424}`
- `{"bin": 4, "count": 2661, "mean_probability": 0.19637931767984082, "observed_rate": 0.22848553175497932}`
- `{"bin": 5, "count": 2661, "mean_probability": 0.3586731646278454, "observed_rate": 0.3543780533633972}`
- `{"bin": 6, "count": 2661, "mean_probability": 0.5646014510742546, "observed_rate": 0.4513340849304773}`
- `{"bin": 7, "count": 2661, "mean_probability": 0.7444573200650936, "observed_rate": 0.6392333709131905}`
- `{"bin": 8, "count": 2661, "mean_probability": 0.8690234708433382, "observed_rate": 0.7985719654265314}`
- `{"bin": 9, "count": 2661, "mean_probability": 0.9529021222022772, "observed_rate": 0.9402480270574972}`
- `{"bin": 10, "count": 2661, "mean_probability": 0.9920275011181999, "observed_rate": 0.9962420142803458}`

#### japan_role

##### japan_chasing

- states: 497
- matches: 4
- brier: 0.01022595746320196
- log_loss: 0.07552110180538826
- match_macro_brier: 0.010374179179522793
- match_macro_log_loss: 0.07608757407184993
- ece: 0.06606705877945604
- calibration_slope: None
- calibration_intercept: None
- roc_auc: None

###### calibration_curve

- `{"bin": 1, "count": 50, "mean_probability": 0.00212783365919099, "observed_rate": 0.0}`
- `{"bin": 2, "count": 50, "mean_probability": 0.008051398424172178, "observed_rate": 0.0}`
- `{"bin": 3, "count": 50, "mean_probability": 0.013984686479389701, "observed_rate": 0.0}`
- `{"bin": 4, "count": 50, "mean_probability": 0.02320562760991826, "observed_rate": 0.0}`
- `{"bin": 5, "count": 50, "mean_probability": 0.03919894007195974, "observed_rate": 0.0}`
- `{"bin": 6, "count": 50, "mean_probability": 0.057354192834103056, "observed_rate": 0.0}`
- `{"bin": 7, "count": 50, "mean_probability": 0.07541368845011046, "observed_rate": 0.0}`
- `{"bin": 8, "count": 49, "mean_probability": 0.09696681243215198, "observed_rate": 0.0}`
- `{"bin": 9, "count": 49, "mean_probability": 0.1287045214683269, "observed_rate": 0.0}`
- `{"bin": 10, "count": 49, "mean_probability": 0.22062478522089735, "observed_rate": 0.0}`

##### japan_defending

- states: 1123
- matches: 10
- brier: 0.11730725334133196
- log_loss: 0.34596008083432717
- match_macro_brier: 0.12213961416595512
- match_macro_log_loss: 0.35734513205437374
- ece: 0.14018775331970457
- calibration_slope: 0.7110196292039194
- calibration_intercept: -1.6361073387004554
- roc_auc: 0.8643902710524851

###### calibration_curve

- `{"bin": 1, "count": 113, "mean_probability": 8.53300071830111e-05, "observed_rate": 0.0}`
- `{"bin": 2, "count": 113, "mean_probability": 0.0030995003156878637, "observed_rate": 0.0}`
- `{"bin": 3, "count": 113, "mean_probability": 0.008248589583146185, "observed_rate": 0.0}`
- `{"bin": 4, "count": 112, "mean_probability": 0.024236995709916602, "observed_rate": 0.0}`
- `{"bin": 5, "count": 112, "mean_probability": 0.07233613838550161, "observed_rate": 0.0}`
- `{"bin": 6, "count": 112, "mean_probability": 0.14086075144548355, "observed_rate": 0.05357142857142857}`
- `{"bin": 7, "count": 112, "mean_probability": 0.24209657805433757, "observed_rate": 0.10714285714285714}`
- `{"bin": 8, "count": 112, "mean_probability": 0.40803911859771314, "observed_rate": 0.21428571428571427}`
- `{"bin": 9, "count": 112, "mean_probability": 0.6099024932264953, "observed_rate": 0.22321428571428573}`
- `{"bin": 10, "count": 112, "mean_probability": 0.8430535543006263, "observed_rate": 0.3482142857142857}`

##### other

- states: 72222
- matches: 667
- brier: 0.10193203249150855
- log_loss: 0.3148393858212377
- match_macro_brier: 0.09087205343919239
- match_macro_log_loss: 0.2834983323658838
- ece: 0.02463063768280859
- calibration_slope: 1.0452553656655577
- calibration_intercept: -0.22375644350490054
- roc_auc: 0.9361331942846758

###### calibration_curve

- `{"bin": 1, "count": 7223, "mean_probability": 0.0005838917095928509, "observed_rate": 0.0}`
- `{"bin": 2, "count": 7223, "mean_probability": 0.008158041572028742, "observed_rate": 0.0004153398864737644}`
- `{"bin": 3, "count": 7222, "mean_probability": 0.03648090349925142, "observed_rate": 0.02076986984214899}`
- `{"bin": 4, "count": 7222, "mean_probability": 0.11835683674584607, "observed_rate": 0.10938798116865134}`
- `{"bin": 5, "count": 7222, "mean_probability": 0.2632981058032697, "observed_rate": 0.2453613957352534}`
- `{"bin": 6, "count": 7222, "mean_probability": 0.456377389470873, "observed_rate": 0.3865965106618665}`
- `{"bin": 7, "count": 7222, "mean_probability": 0.6568871173736356, "observed_rate": 0.5859872611464968}`
- `{"bin": 8, "count": 7222, "mean_probability": 0.8211510017037776, "observed_rate": 0.7783162558847965}`
- `{"bin": 9, "count": 7222, "mean_probability": 0.9305355218895842, "observed_rate": 0.9329825533093326}`
- `{"bin": 10, "count": 7222, "mean_probability": 0.9864396861223766, "observed_rate": 0.9958460260315702}`

#### match_format

##### full

- states: 73842
- matches: 681
- brier: 0.10154862540238965
- log_loss: 0.31370192141539577
- match_macro_brier: 0.09085837371853005
- match_macro_log_loss: 0.2833644483184664
- ece: 0.02654830066070857
- calibration_slope: 1.0461166804247797
- calibration_intercept: -0.24539372763082376
- roc_auc: 0.9363876073529155

###### calibration_curve

- `{"bin": 1, "count": 7385, "mean_probability": 0.0005716512984838079, "observed_rate": 0.0}`
- `{"bin": 2, "count": 7385, "mean_probability": 0.00793727265029207, "observed_rate": 0.00040622884224779957}`
- `{"bin": 3, "count": 7384, "mean_probability": 0.03487583251987209, "observed_rate": 0.01868905742145179}`
- `{"bin": 4, "count": 7384, "mean_probability": 0.11204821709262969, "observed_rate": 0.10197724810400867}`
- `{"bin": 5, "count": 7384, "mean_probability": 0.251471166663629, "observed_rate": 0.22467497291440952}`
- `{"bin": 6, "count": 7384, "mean_probability": 0.4433917813023964, "observed_rate": 0.38068797399783316}`
- `{"bin": 7, "count": 7384, "mean_probability": 0.645679442014533, "observed_rate": 0.5689328277356447}`
- `{"bin": 8, "count": 7384, "mean_probability": 0.8147161718037846, "observed_rate": 0.7608342361863488}`
- `{"bin": 9, "count": 7384, "mean_probability": 0.9278179103896294, "observed_rate": 0.9295774647887324}`
- `{"bin": 10, "count": 7384, "mean_probability": 0.98601946617158, "observed_rate": 0.9952600216684724}`

### selection_model_0

- selected: logistic
- feature_set: model_0
- selection_rule: rolling-origin match-macro Brier with log-loss/ECE guards
- model_1_gate_passed: True

#### candidates

- `{"ece": 0.12960465620209238, "match_macro_brier": 0.18293210168072993, "match_macro_log_loss": 0.5478270101536378, "name": "empirical_12"}`
- `{"ece": 0.12441581411007113, "match_macro_brier": 0.20140082770194204, "match_macro_log_loss": 0.5900405426898707, "name": "empirical_24"}`
- `{"ece": 0.1030640208577182, "match_macro_brier": 0.21633819521180275, "match_macro_log_loss": 0.6230086923843836, "name": "empirical_48"}`
- `{"ece": 0.1384032606568124, "match_macro_brier": 0.22729546357587066, "match_macro_log_loss": 0.6465484940222959, "name": "empirical_96"}`
- `{"ece": 0.025767872589183234, "match_macro_brier": 0.08766530390938063, "match_macro_log_loss": 0.28073289827367287, "name": "logistic"}`
- `{"ece": 0.02463051126762662, "match_macro_brier": 0.09200883419312231, "match_macro_log_loss": 0.2815070248072804, "name": "hgb"}`

### selection_model_1

- selected: logistic
- feature_set: model_1
- selection_rule: Model 1 must improve rolling-origin match-macro Brier
- model_1_gate_passed: True

#### candidates

- `{"ece": 0.12960465620209238, "match_macro_brier": 0.18293210168072993, "match_macro_log_loss": 0.5478270101536378, "name": "empirical_12"}`
- `{"ece": 0.12441581411007113, "match_macro_brier": 0.20140082770194204, "match_macro_log_loss": 0.5900405426898707, "name": "empirical_24"}`
- `{"ece": 0.1030640208577182, "match_macro_brier": 0.21633819521180275, "match_macro_log_loss": 0.6230086923843836, "name": "empirical_48"}`
- `{"ece": 0.1384032606568124, "match_macro_brier": 0.22729546357587066, "match_macro_log_loss": 0.6465484940222959, "name": "empirical_96"}`
- `{"ece": 0.012161611694123308, "match_macro_brier": 0.08581330496566912, "match_macro_log_loss": 0.27572305994208307, "name": "logistic"}`
- `{"ece": 0.028133338328911874, "match_macro_brier": 0.09561407028020362, "match_macro_log_loss": 0.30064696179262695, "name": "hgb"}`

### experimental_reduced

- states: 1390
- matches: 23
- brier: 0.21220286970467367
- log_loss: 0.6280201638244587
- match_macro_brier: 0.2114581688345006
- match_macro_log_loss: 0.6310882091135737
- ece: 0.28634551294257143
- calibration_slope: 2.4388414385042037
- calibration_intercept: -6.653636519686141
- roc_auc: 0.980918466066981

#### calibration_curve

- `{"bin": 1, "count": 139, "mean_probability": 0.01209149707791229, "observed_rate": 0.0}`
- `{"bin": 2, "count": 139, "mean_probability": 0.08677352530971706, "observed_rate": 0.0}`
- `{"bin": 3, "count": 139, "mean_probability": 0.23337131424209742, "observed_rate": 0.0}`
- `{"bin": 4, "count": 139, "mean_probability": 0.5168977679040098, "observed_rate": 0.0}`
- `{"bin": 5, "count": 139, "mean_probability": 0.7184532376877915, "observed_rate": 0.03597122302158273}`
- `{"bin": 6, "count": 139, "mean_probability": 0.8690641121580901, "observed_rate": 0.06474820143884892}`
- `{"bin": 7, "count": 139, "mean_probability": 0.9384954721432749, "observed_rate": 0.5611510791366906}`
- `{"bin": 8, "count": 139, "mean_probability": 0.9678456447100319, "observed_rate": 0.8201438848920863}`
- `{"bin": 9, "count": 139, "mean_probability": 0.9846663989919404, "observed_rate": 0.9856115107913669}`
- `{"bin": 10, "count": 139, "mean_probability": 0.9943375902782549, "observed_rate": 0.9928057553956835}`

## verification

- status: recomputed_from_frozen_predictions
- source_sha256: acb457e9d1337907e901b4aa08a3a8a1962a7b98b216476ca3236d595bb0f4d9

### first_innings

#### locked_test

- states: 88417
- matches: 685
- mae: 15.98264723795996
- rmse: 22.970731197552325
- match_macro_mae: 16.27641884094087
- match_macro_rmse: 20.857601716833955

#### by_slice

##### legal_over

###### 0

- states: 4577
- matches: 685
- mae: 33.19802555999492
- rmse: 41.79589865906517
- match_macro_mae: 32.83379175087569
- match_macro_rmse: 34.00216337161456

###### 1

- states: 4571
- matches: 685
- mae: 30.238235651301466
- rmse: 38.515338157583265
- match_macro_mae: 29.854500391456657
- match_macro_rmse: 30.897402080427828

###### 10

- states: 4510
- matches: 682
- mae: 13.968254859963379
- rmse: 17.75719473228847
- match_macro_mae: 13.961535752791992
- match_macro_rmse: 14.29971729014384

###### 11

- states: 4477
- matches: 681
- mae: 12.747146311066354
- rmse: 16.082405144948478
- match_macro_mae: 12.709228469149911
- match_macro_rmse: 13.02860616670169

###### 12

- states: 4426
- matches: 679
- mae: 11.48618920201933
- rmse: 14.491756590767535
- match_macro_mae: 11.484676219965026
- match_macro_rmse: 11.771613974704534

###### 13

- states: 4416
- matches: 674
- mae: 10.301133919112942
- rmse: 13.013155570858439
- match_macro_mae: 10.306222398086094
- match_macro_rmse: 10.559666690898917

###### 14

- states: 4342
- matches: 668
- mae: 9.164974352920673
- rmse: 11.669685583162556
- match_macro_mae: 9.1395209003852
- match_macro_rmse: 9.406701907782443

###### 15

- states: 4256
- matches: 660
- mae: 8.091290195248318
- rmse: 10.352389904646023
- match_macro_mae: 7.996001512265466
- match_macro_rmse: 8.236568433073527

###### 16

- states: 4257
- matches: 652
- mae: 6.684960814870737
- rmse: 8.609129448361013
- match_macro_mae: 6.690345870390438
- match_macro_rmse: 6.934233679266055

###### 17

- states: 4172
- matches: 643
- mae: 5.445788387679216
- rmse: 7.039883485728678
- match_macro_mae: 5.473177491242251
- match_macro_rmse: 5.725891178804882

###### 18

- states: 4069
- matches: 631
- mae: 4.31174991761907
- rmse: 5.597724109873522
- match_macro_mae: 4.271560168423063
- match_macro_rmse: 4.529961231950051

###### 19

- states: 3951
- matches: 619
- mae: 2.33644143095616
- rmse: 3.1322073832550146
- match_macro_mae: 2.3078168466971785
- match_macro_rmse: 2.6363431775429227

###### 2

- states: 4473
- matches: 685
- mae: 27.89562821607813
- rmse: 35.080794381790156
- match_macro_mae: 27.823850720194525
- match_macro_rmse: 28.658846460157804

###### 20

- states: 581
- matches: 581
- mae: 0.0
- rmse: 0.0
- match_macro_mae: 0.0
- match_macro_rmse: 0.0

###### 3

- states: 4441
- matches: 685
- mae: 26.042348256211586
- rmse: 32.07943050033726
- match_macro_mae: 26.00886990728521
- match_macro_rmse: 26.735167188602915

###### 4

- states: 4506
- matches: 685
- mae: 24.40019749698852
- rmse: 30.578470636497947
- match_macro_mae: 24.1511782583662
- match_macro_rmse: 24.78710767673934

###### 5

- states: 4516
- matches: 685
- mae: 21.83496037759207
- rmse: 27.048765715244105
- match_macro_mae: 21.671852764633467
- match_macro_rmse: 22.201613531669942

###### 6

- states: 4447
- matches: 685
- mae: 19.16681003701385
- rmse: 23.835580437767863
- match_macro_mae: 19.173797259966168
- match_macro_rmse: 19.603905151718124

###### 7

- states: 4466
- matches: 685
- mae: 17.572187939457955
- rmse: 22.002411643611175
- match_macro_mae: 17.52088258495027
- match_macro_rmse: 17.925795701460746

###### 8

- states: 4481
- matches: 684
- mae: 16.34200036521146
- rmse: 20.664746108886142
- match_macro_mae: 16.313806576421754
- match_macro_rmse: 16.687985317358

###### 9

- states: 4482
- matches: 683
- mae: 15.276141692683753
- rmse: 19.416053363563215
- match_macro_mae: 15.123328348221136
- match_macro_rmse: 15.466303354118585

##### phase_absolute

###### death

- states: 17030
- matches: 652
- mae: 4.577422069923793
- rmse: 6.3585517292697915
- match_macro_mae: 4.622262501343993
- match_macro_rmse: 5.449811375804268

###### middle

- states: 44303
- matches: 685
- mae: 13.453551683513952
- rmse: 17.51847849146925
- match_macro_mae: 13.443966931604697
- match_macro_rmse: 15.287900020862025

###### powerplay

- states: 27084
- matches: 685
- mae: 27.291076752074467
- rmse: 34.57050360410424
- match_macro_mae: 27.13957812561087
- match_macro_rmse: 30.017116048510346

##### phase_relative

###### death

- states: 17030
- matches: 652
- mae: 4.577422069923793
- rmse: 6.3585517292697915
- match_macro_mae: 4.622262501343993
- match_macro_rmse: 5.449811375804268

###### middle

- states: 44303
- matches: 685
- mae: 13.453551683513952
- rmse: 17.51847849146925
- match_macro_mae: 13.443966931604697
- match_macro_rmse: 15.287900020862025

###### powerplay

- states: 27084
- matches: 685
- mae: 27.291076752074467
- rmse: 34.57050360410424
- match_macro_mae: 27.13957812561087
- match_macro_rmse: 30.017116048510346

##### japan_role

###### japan_batting

- states: 1313
- matches: 10
- mae: 13.466397696924526
- rmse: 18.404417962909353
- match_macro_mae: 13.361401906468132
- match_macro_rmse: 17.154430827069184

###### japan_bowling

- states: 504
- matches: 4
- mae: 13.520913409224757
- rmse: 17.75973556185074
- match_macro_mae: 13.488948511901057
- match_macro_rmse: 17.034786191152627

###### other

- states: 86600
- matches: 671
- mae: 16.035124714831344
- rmse: 23.059797426373166
- match_macro_mae: 16.336478528960075
- match_macro_rmse: 20.935579318920947

##### match_format

###### full

- states: 88417
- matches: 685
- mae: 15.98264723795996
- rmse: 22.970731197552325
- match_macro_mae: 16.27641884094087
- match_macro_rmse: 20.857601716833955

#### intervals

##### overall

###### p50

- nominal_coverage: 0.5
- coverage: 0.5090876188968185
- mean_width: 26.511920626293286
- interval_score: 50.84355985222352

###### p80

- nominal_coverage: 0.8
- coverage: 0.7990771005575851
- mean_width: 50.23833621480344
- interval_score: 69.97117679983657

##### by_slice

###### legal_over

###### 0

- states: 4577
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.47279877649115143
- mean_width: 51.99883434316422
- interval_score: 106.8881022829852

###### p80

- nominal_coverage: 0.8
- coverage: 0.7734323792877431
- mean_width: 102.4385681819378
- interval_score: 147.36446082821098

###### 1

- states: 4571
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.49989061474513236
- mean_width: 49.196669931659706
- interval_score: 97.83565104624495

###### p80

- nominal_coverage: 0.8
- coverage: 0.7700721942682126
- mean_width: 93.9219102343916
- interval_score: 138.20784827828388

###### 10

- states: 4510
- matches: 682

###### p50

- nominal_coverage: 0.5
- coverage: 0.5144124168514412
- mean_width: 24.48268523462253
- interval_score: 44.37523165175304

###### p80

- nominal_coverage: 0.8
- coverage: 0.7955654101995565
- mean_width: 44.44340078161429
- interval_score: 61.94335856803514

###### 11

- states: 4477
- matches: 681

###### p50

- nominal_coverage: 0.5
- coverage: 0.5101630556176011
- mean_width: 22.22549445057791
- interval_score: 40.30865698060512

###### p80

- nominal_coverage: 0.8
- coverage: 0.8058968058968059
- mean_width: 40.63963647779183
- interval_score: 55.701357627219394

###### 12

- states: 4426
- matches: 679

###### p50

- nominal_coverage: 0.5
- coverage: 0.49932218707636694
- mean_width: 19.684047249440063
- interval_score: 36.29255290959269

###### p80

- nominal_coverage: 0.8
- coverage: 0.807049254405784
- mean_width: 36.628651250964005
- interval_score: 49.64532452063429

###### 13

- states: 4416
- matches: 674

###### p50

- nominal_coverage: 0.5
- coverage: 0.5047554347826086
- mean_width: 17.95310169245012
- interval_score: 32.75109465585294

###### p80

- nominal_coverage: 0.8
- coverage: 0.8249547101449275
- mean_width: 34.05970371219737
- interval_score: 44.7751166364774

###### 14

- states: 4342
- matches: 668

###### p50

- nominal_coverage: 0.5
- coverage: 0.5246430216490097
- mean_width: 16.516490347959795
- interval_score: 29.503629544089616

###### p80

- nominal_coverage: 0.8
- coverage: 0.8141409488714878
- mean_width: 30.597165850895454
- interval_score: 40.45839410065759

###### 15

- states: 4256
- matches: 660

###### p50

- nominal_coverage: 0.5
- coverage: 0.5082236842105263
- mean_width: 13.903017972719844
- interval_score: 25.952500249944112

###### p80

- nominal_coverage: 0.8
- coverage: 0.7974624060150376
- mean_width: 26.042719388649754
- interval_score: 36.34253727935347

###### 16

- states: 4257
- matches: 652

###### p50

- nominal_coverage: 0.5
- coverage: 0.551092318534179
- mean_width: 12.278865041083767
- interval_score: 21.652151258119634

###### p80

- nominal_coverage: 0.8
- coverage: 0.8205308902983321
- mean_width: 22.583987628689254
- interval_score: 30.341442927411666

###### 17

- states: 4172
- matches: 643

###### p50

- nominal_coverage: 0.5
- coverage: 0.5711888782358581
- mean_width: 10.366966415146702
- interval_score: 17.610914485494277

###### p80

- nominal_coverage: 0.8
- coverage: 0.8267018216682647
- mean_width: 18.698857121862012
- interval_score: 24.71602957572684

###### 18

- states: 4069
- matches: 631

###### p50

- nominal_coverage: 0.5
- coverage: 0.5394445809781273
- mean_width: 7.811239636649153
- interval_score: 13.862976639092835

###### p80

- nominal_coverage: 0.8
- coverage: 0.805111821086262
- mean_width: 13.851632502123346
- interval_score: 19.29564270034897

###### 19

- states: 3951
- matches: 619

###### p50

- nominal_coverage: 0.5
- coverage: 0.5828904074917742
- mean_width: 4.48017736701479
- interval_score: 7.446236019513114

###### p80

- nominal_coverage: 0.8
- coverage: 0.8683877499367249
- mean_width: 8.198187507953733
- interval_score: 10.316332368720131

###### 2

- states: 4473
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.4846858931365974
- mean_width: 44.51725846218585
- interval_score: 89.3484508955795

###### p80

- nominal_coverage: 0.8
- coverage: 0.7672702883970489
- mean_width: 85.58545178450044
- interval_score: 125.39013945855642

###### 20

- states: 581
- matches: 581

###### p50

- nominal_coverage: 0.5
- coverage: 1.0
- mean_width: 0.0
- interval_score: 0.0

###### p80

- nominal_coverage: 0.8
- coverage: 1.0
- mean_width: 0.0
- interval_score: 0.0

###### 3

- states: 4441
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.4683629813105156
- mean_width: 41.26884337372448
- interval_score: 82.06787265883116

###### p80

- nominal_coverage: 0.8
- coverage: 0.7725737446521054
- mean_width: 79.1183892593448
- interval_score: 110.90588314014688

###### 4

- states: 4506
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.47003994673768307
- mean_width: 38.30037077615331
- interval_score: 75.29461425982572

###### p80

- nominal_coverage: 0.8
- coverage: 0.7758544163337772
- mean_width: 72.70187669820194
- interval_score: 100.5163748104516

###### 5

- states: 4516
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.46811337466784764
- mean_width: 34.9754582417144
- interval_score: 68.2455331015771

###### p80

- nominal_coverage: 0.8
- coverage: 0.7632860938883969
- mean_width: 66.0368187064959
- interval_score: 91.79192788241254

###### 6

- states: 4447
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.48639532268945357
- mean_width: 32.46858586933948
- interval_score: 60.526167376916554

###### p80

- nominal_coverage: 0.8
- coverage: 0.7908702496064762
- mean_width: 60.733139450351274
- interval_score: 81.58042008608948

###### 7

- states: 4466
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.49664128974473803
- mean_width: 29.842524170220845
- interval_score: 55.76365220051964

###### p80

- nominal_coverage: 0.8
- coverage: 0.7987012987012987
- mean_width: 56.98454180073392
- interval_score: 76.55850992494153

###### 8

- states: 4481
- matches: 684

###### p50

- nominal_coverage: 0.5
- coverage: 0.4898460165141709
- mean_width: 27.33884384806607
- interval_score: 52.320781235999256

###### p80

- nominal_coverage: 0.8
- coverage: 0.8013836197277393
- mean_width: 53.057023342388355
- interval_score: 71.75826859869828

###### 9

- states: 4482
- matches: 683

###### p50

- nominal_coverage: 0.5
- coverage: 0.49419901829540386
- mean_width: 25.86137587034006
- interval_score: 48.83341511718482

###### p80

- nominal_coverage: 0.8
- coverage: 0.7900490852298081
- mean_width: 49.06565318478058
- interval_score: 68.09536157904071

###### phase_absolute

###### death

- states: 17030
- matches: 652

###### p50

- nominal_coverage: 0.5
- coverage: 0.5759248385202583
- mean_width: 8.51481075880719
- interval_score: 14.766557463115822

###### p80

- nominal_coverage: 0.8
- coverage: 0.8355842630651791
- mean_width: 15.437756825766504
- interval_score: 20.643135482587027

###### middle

- states: 44303
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.5027876216057603
- mean_width: 23.09751811582084
- interval_score: 42.79469900684563

###### p80

- nominal_coverage: 0.8
- coverage: 0.8025641604406022
- mean_width: 43.35675177522707
- interval_score: 58.867152971933066

###### powerplay

- states: 27084
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.4773667109732683
- mean_width: 43.413377407594005
- interval_score: 86.69424781261638

###### p80

- nominal_coverage: 0.8
- coverage: 0.770417958942549
- mean_width: 83.3770418130109
- interval_score: 119.15143493306536

###### phase_relative

###### death

- states: 17030
- matches: 652

###### p50

- nominal_coverage: 0.5
- coverage: 0.5759248385202583
- mean_width: 8.51481075880719
- interval_score: 14.766557463115822

###### p80

- nominal_coverage: 0.8
- coverage: 0.8355842630651791
- mean_width: 15.437756825766504
- interval_score: 20.643135482587027

###### middle

- states: 44303
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.5027876216057603
- mean_width: 23.09751811582084
- interval_score: 42.79469900684563

###### p80

- nominal_coverage: 0.8
- coverage: 0.8025641604406022
- mean_width: 43.35675177522707
- interval_score: 58.867152971933066

###### powerplay

- states: 27084
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.4773667109732683
- mean_width: 43.413377407594005
- interval_score: 86.69424781261638

###### p80

- nominal_coverage: 0.8
- coverage: 0.770417958942549
- mean_width: 83.3770418130109
- interval_score: 119.15143493306536

###### japan_role

###### japan_batting

- states: 1313
- matches: 10

###### p50

- nominal_coverage: 0.5
- coverage: 0.555978674790556
- mean_width: 27.124155216962002
- interval_score: 41.19023556490175

###### p80

- nominal_coverage: 0.8
- coverage: 0.8918507235338918
- mean_width: 51.371723146886474
- interval_score: 56.57630563154215

###### japan_bowling

- states: 504
- matches: 4

###### p50

- nominal_coverage: 0.5
- coverage: 0.501984126984127
- mean_width: 24.698245629449207
- interval_score: 40.966348310582276

###### p80

- nominal_coverage: 0.8
- coverage: 0.875
- mean_width: 46.88864125349852
- interval_score: 54.92886639026316

###### other

- states: 86600
- matches: 671

###### p50

- nominal_coverage: 0.5
- coverage: 0.508418013856813
- mean_width: 26.513193469028405
- interval_score: 51.047404302642

###### p80

- nominal_coverage: 0.8
- coverage: 0.7972286374133949
- mean_width: 50.24064694481121
- interval_score: 70.26180948217372

###### match_format

###### full

- states: 88417
- matches: 685

###### p50

- nominal_coverage: 0.5
- coverage: 0.5090876188968185
- mean_width: 26.511920626293286
- interval_score: 50.84355985222352

###### p80

- nominal_coverage: 0.8
- coverage: 0.7990771005575851
- mean_width: 50.23833621480344
- interval_score: 69.97117679983657

### chase

#### locked_test_nonterminal

- states: 73842
- matches: 681
- brier: 0.10154862540238965
- log_loss: 0.31370192141539577
- match_macro_brier: 0.09085837371853005
- match_macro_log_loss: 0.2833644483184664
- ece: 0.02654830066070857
- calibration_slope: 1.0461166804247797
- calibration_intercept: -0.24539372763082376
- roc_auc: 0.9363876073529155

##### calibration_curve

- `{"bin": 1, "count": 7385, "mean_probability": 0.0005716512984838079, "observed_rate": 0.0}`
- `{"bin": 2, "count": 7385, "mean_probability": 0.00793727265029207, "observed_rate": 0.00040622884224779957}`
- `{"bin": 3, "count": 7384, "mean_probability": 0.03487583251987209, "observed_rate": 0.01868905742145179}`
- `{"bin": 4, "count": 7384, "mean_probability": 0.11204821709262969, "observed_rate": 0.10197724810400867}`
- `{"bin": 5, "count": 7384, "mean_probability": 0.251471166663629, "observed_rate": 0.22467497291440952}`
- `{"bin": 6, "count": 7384, "mean_probability": 0.4433917813023964, "observed_rate": 0.38068797399783316}`
- `{"bin": 7, "count": 7384, "mean_probability": 0.645679442014533, "observed_rate": 0.5689328277356447}`
- `{"bin": 8, "count": 7384, "mean_probability": 0.8147161718037846, "observed_rate": 0.7608342361863488}`
- `{"bin": 9, "count": 7384, "mean_probability": 0.9278179103896294, "observed_rate": 0.9295774647887324}`
- `{"bin": 10, "count": 7384, "mean_probability": 0.98601946617158, "observed_rate": 0.9952600216684724}`

#### by_slice

##### legal_over

###### 0

- states: 4503
- matches: 681
- brier: 0.15724194279981318
- log_loss: 0.47956071780709086
- match_macro_brier: 0.15728830971463076
- match_macro_log_loss: 0.47845521669492336
- ece: 0.07139193292733532
- calibration_slope: 0.6467399554328345
- calibration_intercept: -0.061442126627096985
- roc_auc: 0.8632127210387632

###### calibration_curve

- `{"bin": 1, "count": 451, "mean_probability": 0.003980618956681263, "observed_rate": 0.0022172949002217295}`
- `{"bin": 2, "count": 451, "mean_probability": 0.026745100472907592, "observed_rate": 0.08869179600886919}`
- `{"bin": 3, "count": 451, "mean_probability": 0.08201309339651523, "observed_rate": 0.2328159645232816}`
- `{"bin": 4, "count": 450, "mean_probability": 0.1914662970965061, "observed_rate": 0.2311111111111111}`
- `{"bin": 5, "count": 450, "mean_probability": 0.3415158049488943, "observed_rate": 0.4177777777777778}`
- `{"bin": 6, "count": 450, "mean_probability": 0.5248449581867106, "observed_rate": 0.4866666666666667}`
- `{"bin": 7, "count": 450, "mean_probability": 0.7126505957678994, "observed_rate": 0.5888888888888889}`
- `{"bin": 8, "count": 450, "mean_probability": 0.8539012928990711, "observed_rate": 0.7088888888888889}`
- `{"bin": 9, "count": 450, "mean_probability": 0.9486771487906045, "observed_rate": 0.8866666666666667}`
- `{"bin": 10, "count": 450, "mean_probability": 0.9923137958620868, "observed_rate": 0.9777777777777777}`

###### 1

- states: 4518
- matches: 680
- brier: 0.13845708410041838
- log_loss: 0.41563678333562554
- match_macro_brier: 0.13947685541841034
- match_macro_log_loss: 0.41850270122180816
- ece: 0.05614309006207722
- calibration_slope: 0.7893039026549807
- calibration_intercept: -0.16890402726692547
- roc_auc: 0.8917101067309374

###### calibration_curve

- `{"bin": 1, "count": 452, "mean_probability": 0.0046009772191946035, "observed_rate": 0.0}`
- `{"bin": 2, "count": 452, "mean_probability": 0.029850876978243103, "observed_rate": 0.030973451327433628}`
- `{"bin": 3, "count": 452, "mean_probability": 0.09267508001416842, "observed_rate": 0.17699115044247787}`
- `{"bin": 4, "count": 452, "mean_probability": 0.21613747357915192, "observed_rate": 0.2920353982300885}`
- `{"bin": 5, "count": 452, "mean_probability": 0.3795020180462285, "observed_rate": 0.32079646017699115}`
- `{"bin": 6, "count": 452, "mean_probability": 0.5743282889347844, "observed_rate": 0.48451327433628316}`
- `{"bin": 7, "count": 452, "mean_probability": 0.7375848314628266, "observed_rate": 0.6637168141592921}`
- `{"bin": 8, "count": 452, "mean_probability": 0.8726268164622963, "observed_rate": 0.7278761061946902}`
- `{"bin": 9, "count": 451, "mean_probability": 0.9555547277337518, "observed_rate": 0.9356984478935698}`
- `{"bin": 10, "count": 451, "mean_probability": 0.9916883281812858, "observed_rate": 1.0}`

###### 10

- states: 3935
- matches: 611
- brier: 0.09171457470866999
- log_loss: 0.2876339546485484
- match_macro_brier: 0.09186899607073887
- match_macro_log_loss: 0.28801984140539477
- ece: 0.03262669961839362
- calibration_slope: 1.2212718318229787
- calibration_intercept: -0.3194452679666984
- roc_auc: 0.9488773062874395

###### calibration_curve

- `{"bin": 1, "count": 394, "mean_probability": 0.0008542235050984433, "observed_rate": 0.0}`
- `{"bin": 2, "count": 394, "mean_probability": 0.008493880489618804, "observed_rate": 0.0}`
- `{"bin": 3, "count": 394, "mean_probability": 0.03623512601958683, "observed_rate": 0.005076142131979695}`
- `{"bin": 4, "count": 394, "mean_probability": 0.11708576446799203, "observed_rate": 0.07106598984771574}`
- `{"bin": 5, "count": 394, "mean_probability": 0.27503981922523874, "observed_rate": 0.17766497461928935}`
- `{"bin": 6, "count": 393, "mean_probability": 0.46544354385127584, "observed_rate": 0.44783715012722647}`
- `{"bin": 7, "count": 393, "mean_probability": 0.6643939508256147, "observed_rate": 0.5699745547073791}`
- `{"bin": 8, "count": 393, "mean_probability": 0.818335675836409, "observed_rate": 0.8269720101781171}`
- `{"bin": 9, "count": 393, "mean_probability": 0.9307307448206458, "observed_rate": 0.9236641221374046}`
- `{"bin": 10, "count": 393, "mean_probability": 0.9854163031074119, "observed_rate": 1.0}`

###### 11

- states: 3845
- matches: 597
- brier: 0.08782729057234717
- log_loss: 0.2755174965887238
- match_macro_brier: 0.08787609705553176
- match_macro_log_loss: 0.2758545011469222
- ece: 0.03890415988595386
- calibration_slope: 1.3147568713465851
- calibration_intercept: -0.3566802268101363
- roc_auc: 0.9535420625779416

###### calibration_curve

- `{"bin": 1, "count": 385, "mean_probability": 0.0006949678159166204, "observed_rate": 0.0}`
- `{"bin": 2, "count": 385, "mean_probability": 0.006916848660581941, "observed_rate": 0.0}`
- `{"bin": 3, "count": 385, "mean_probability": 0.029525587263681076, "observed_rate": 0.0}`
- `{"bin": 4, "count": 385, "mean_probability": 0.10642771313298262, "observed_rate": 0.07012987012987013}`
- `{"bin": 5, "count": 385, "mean_probability": 0.26721368677725915, "observed_rate": 0.15064935064935064}`
- `{"bin": 6, "count": 384, "mean_probability": 0.4660377342865649, "observed_rate": 0.390625}`
- `{"bin": 7, "count": 384, "mean_probability": 0.6255777063422902, "observed_rate": 0.5494791666666666}`
- `{"bin": 8, "count": 384, "mean_probability": 0.8144029284226956, "observed_rate": 0.828125}`
- `{"bin": 9, "count": 384, "mean_probability": 0.9269501482325477, "observed_rate": 0.9453125}`
- `{"bin": 10, "count": 384, "mean_probability": 0.9845419073171526, "observed_rate": 1.0}`

###### 12

- states: 3656
- matches: 580
- brier: 0.08857057193244895
- log_loss: 0.2775278781659798
- match_macro_brier: 0.08721575648318677
- match_macro_log_loss: 0.27309461809737473
- ece: 0.03285572071514402
- calibration_slope: 1.3131496676863055
- calibration_intercept: -0.292867421851404
- roc_auc: 0.9518313738517717

###### calibration_curve

- `{"bin": 1, "count": 366, "mean_probability": 0.0006208971301973503, "observed_rate": 0.0}`
- `{"bin": 2, "count": 366, "mean_probability": 0.006212437071417864, "observed_rate": 0.0}`
- `{"bin": 3, "count": 366, "mean_probability": 0.02432861009477526, "observed_rate": 0.0}`
- `{"bin": 4, "count": 366, "mean_probability": 0.08841706303829851, "observed_rate": 0.04918032786885246}`
- `{"bin": 5, "count": 366, "mean_probability": 0.23185896261475386, "observed_rate": 0.12568306010928962}`
- `{"bin": 6, "count": 366, "mean_probability": 0.427098833706412, "observed_rate": 0.366120218579235}`
- `{"bin": 7, "count": 365, "mean_probability": 0.5922097373144429, "observed_rate": 0.547945205479452}`
- `{"bin": 8, "count": 365, "mean_probability": 0.7793788679285141, "observed_rate": 0.7726027397260274}`
- `{"bin": 9, "count": 365, "mean_probability": 0.9052438295437834, "observed_rate": 0.9232876712328767}`
- `{"bin": 10, "count": 365, "mean_probability": 0.9781912283114376, "observed_rate": 1.0}`

###### 13

- states: 3552
- matches: 553
- brier: 0.08441117858491844
- log_loss: 0.2683770936444547
- match_macro_brier: 0.08300345661202568
- match_macro_log_loss: 0.2634897485519805
- ece: 0.03891076307117986
- calibration_slope: 1.3814301911309268
- calibration_intercept: -0.30942900831248465
- roc_auc: 0.9556980647092892

###### calibration_curve

- `{"bin": 1, "count": 356, "mean_probability": 0.0004519507672196805, "observed_rate": 0.0}`
- `{"bin": 2, "count": 356, "mean_probability": 0.004897110411198106, "observed_rate": 0.0}`
- `{"bin": 3, "count": 355, "mean_probability": 0.021008047208361646, "observed_rate": 0.0}`
- `{"bin": 4, "count": 355, "mean_probability": 0.07604673626156963, "observed_rate": 0.022535211267605635}`
- `{"bin": 5, "count": 355, "mean_probability": 0.1938920467763542, "observed_rate": 0.11267605633802817}`
- `{"bin": 6, "count": 355, "mean_probability": 0.3815683942700118, "observed_rate": 0.22253521126760564}`
- `{"bin": 7, "count": 355, "mean_probability": 0.5645760284418995, "observed_rate": 0.5830985915492958}`
- `{"bin": 8, "count": 355, "mean_probability": 0.7352421541089399, "observed_rate": 0.7295774647887324}`
- `{"bin": 9, "count": 355, "mean_probability": 0.8924632740572176, "observed_rate": 0.9098591549295775}`
- `{"bin": 10, "count": 355, "mean_probability": 0.9723891616210099, "observed_rate": 1.0}`

###### 14

- states: 3329
- matches: 525
- brier: 0.08205817135385594
- log_loss: 0.2606454835253628
- match_macro_brier: 0.08187243588352926
- match_macro_log_loss: 0.2600605971899165
- ece: 0.03369397214812155
- calibration_slope: 1.392033764493916
- calibration_intercept: -0.2801809274667599
- roc_auc: 0.9570315549706826

###### calibration_curve

- `{"bin": 1, "count": 333, "mean_probability": 0.0002974220687888082, "observed_rate": 0.0}`
- `{"bin": 2, "count": 333, "mean_probability": 0.0028141534867756257, "observed_rate": 0.0}`
- `{"bin": 3, "count": 333, "mean_probability": 0.015809550397599178, "observed_rate": 0.0}`
- `{"bin": 4, "count": 333, "mean_probability": 0.05646841618570371, "observed_rate": 0.003003003003003003}`
- `{"bin": 5, "count": 333, "mean_probability": 0.16456490695437126, "observed_rate": 0.08708708708708708}`
- `{"bin": 6, "count": 333, "mean_probability": 0.3300956341063698, "observed_rate": 0.2132132132132132}`
- `{"bin": 7, "count": 333, "mean_probability": 0.5159529195315234, "observed_rate": 0.4954954954954955}`
- `{"bin": 8, "count": 333, "mean_probability": 0.7120800407495202, "observed_rate": 0.7267267267267268}`
- `{"bin": 9, "count": 333, "mean_probability": 0.8723765818629005, "observed_rate": 0.8708708708708709}`
- `{"bin": 10, "count": 332, "mean_probability": 0.96641721331062, "observed_rate": 1.0}`

###### 15

- states: 3080
- matches: 495
- brier: 0.0818012853125018
- log_loss: 0.2581040832082323
- match_macro_brier: 0.08083834607337216
- match_macro_log_loss: 0.25529118274326146
- ece: 0.03416531184754097
- calibration_slope: 1.3303870464596335
- calibration_intercept: -0.24003889977647308
- roc_auc: 0.955742864283348

###### calibration_curve

- `{"bin": 1, "count": 308, "mean_probability": 0.0001918207202977945, "observed_rate": 0.0}`
- `{"bin": 2, "count": 308, "mean_probability": 0.0018917234992264918, "observed_rate": 0.0}`
- `{"bin": 3, "count": 308, "mean_probability": 0.010215953186006954, "observed_rate": 0.0}`
- `{"bin": 4, "count": 308, "mean_probability": 0.04440109428867931, "observed_rate": 0.0}`
- `{"bin": 5, "count": 308, "mean_probability": 0.1323181076593074, "observed_rate": 0.022727272727272728}`
- `{"bin": 6, "count": 308, "mean_probability": 0.27951095731378695, "observed_rate": 0.2435064935064935}`
- `{"bin": 7, "count": 308, "mean_probability": 0.46172065147463043, "observed_rate": 0.4383116883116883}`
- `{"bin": 8, "count": 308, "mean_probability": 0.6765159668944757, "observed_rate": 0.698051948051948}`
- `{"bin": 9, "count": 308, "mean_probability": 0.8539327487466869, "observed_rate": 0.7987012987012987}`
- `{"bin": 10, "count": 308, "mean_probability": 0.9608191663239316, "observed_rate": 1.0}`

###### 16

- states: 2905
- matches: 465
- brier: 0.07959743551856817
- log_loss: 0.25282904179884397
- match_macro_brier: 0.07727178658627624
- match_macro_log_loss: 0.246479412671166
- ece: 0.043654559843307544
- calibration_slope: 1.3237219815053762
- calibration_intercept: -0.1964427169681251
- roc_auc: 0.9563182263297787

###### calibration_curve

- `{"bin": 1, "count": 291, "mean_probability": 9.636649624493504e-05, "observed_rate": 0.0}`
- `{"bin": 2, "count": 291, "mean_probability": 0.000976555290231516, "observed_rate": 0.0}`
- `{"bin": 3, "count": 291, "mean_probability": 0.00716495873248031, "observed_rate": 0.0}`
- `{"bin": 4, "count": 291, "mean_probability": 0.03247266210805066, "observed_rate": 0.0}`
- `{"bin": 5, "count": 291, "mean_probability": 0.10792607398133137, "observed_rate": 0.054982817869415807}`
- `{"bin": 6, "count": 290, "mean_probability": 0.23804174820781765, "observed_rate": 0.10689655172413794}`
- `{"bin": 7, "count": 290, "mean_probability": 0.4177363951274557, "observed_rate": 0.36551724137931035}`
- `{"bin": 8, "count": 290, "mean_probability": 0.6169737081735372, "observed_rate": 0.7}`
- `{"bin": 9, "count": 290, "mean_probability": 0.8261037141914341, "observed_rate": 0.7862068965517242}`
- `{"bin": 10, "count": 290, "mean_probability": 0.9560693875884052, "observed_rate": 0.993103448275862}`

###### 17

- states: 2515
- matches: 415
- brier: 0.07888247492102246
- log_loss: 0.2525341761459901
- match_macro_brier: 0.07544812793105989
- match_macro_log_loss: 0.2424382415013132
- ece: 0.03974667333464096
- calibration_slope: 1.3222729775681608
- calibration_intercept: -0.15331173318917352
- roc_auc: 0.9539213683011707

###### calibration_curve

- `{"bin": 1, "count": 252, "mean_probability": 3.6056720822463284e-05, "observed_rate": 0.0}`
- `{"bin": 2, "count": 252, "mean_probability": 0.0005768182167785707, "observed_rate": 0.0}`
- `{"bin": 3, "count": 252, "mean_probability": 0.005352124751499319, "observed_rate": 0.0}`
- `{"bin": 4, "count": 252, "mean_probability": 0.027222572362858584, "observed_rate": 0.0}`
- `{"bin": 5, "count": 252, "mean_probability": 0.08585538089483534, "observed_rate": 0.047619047619047616}`
- `{"bin": 6, "count": 251, "mean_probability": 0.2010199022114286, "observed_rate": 0.06772908366533864}`
- `{"bin": 7, "count": 251, "mean_probability": 0.3515494577367394, "observed_rate": 0.2788844621513944}`
- `{"bin": 8, "count": 251, "mean_probability": 0.5586580038821962, "observed_rate": 0.6294820717131474}`
- `{"bin": 9, "count": 251, "mean_probability": 0.7732872895155294, "observed_rate": 0.8127490039840638}`
- `{"bin": 10, "count": 251, "mean_probability": 0.9346112294417083, "observed_rate": 0.9243027888446215}`

###### 18

- states: 2136
- matches: 356
- brier: 0.07443080395127029
- log_loss: 0.23334132154020548
- match_macro_brier: 0.07089351668259375
- match_macro_log_loss: 0.22419203539961696
- ece: 0.029871958308417483
- calibration_slope: 1.1561975178066124
- calibration_intercept: -0.18497773924383074
- roc_auc: 0.9524665890452566

###### calibration_curve

- `{"bin": 1, "count": 214, "mean_probability": 3.2330466841307185e-06, "observed_rate": 0.0}`
- `{"bin": 2, "count": 214, "mean_probability": 0.00011737259191438532, "observed_rate": 0.0}`
- `{"bin": 3, "count": 214, "mean_probability": 0.0014934146309887608, "observed_rate": 0.0}`
- `{"bin": 4, "count": 214, "mean_probability": 0.00932243764197177, "observed_rate": 0.0}`
- `{"bin": 5, "count": 214, "mean_probability": 0.038608958352840506, "observed_rate": 0.0}`
- `{"bin": 6, "count": 214, "mean_probability": 0.10515908118333742, "observed_rate": 0.018691588785046728}`
- `{"bin": 7, "count": 213, "mean_probability": 0.22323273773744567, "observed_rate": 0.2676056338028169}`
- `{"bin": 8, "count": 213, "mean_probability": 0.4211830905964866, "observed_rate": 0.3474178403755869}`
- `{"bin": 9, "count": 213, "mean_probability": 0.7020270066353621, "observed_rate": 0.7183098591549296}`
- `{"bin": 10, "count": 213, "mean_probability": 0.911117688954556, "observed_rate": 0.8826291079812206}`

###### 19

- states: 1652
- matches: 289
- brier: 0.04906247561514167
- log_loss: 0.15257180918093358
- match_macro_brier: 0.055848801136221975
- match_macro_log_loss: 0.17293890362103592
- ece: 0.013330812290974249
- calibration_slope: 1.0050104253057117
- calibration_intercept: -0.1768580004808554
- roc_auc: 0.9588585655462989

###### calibration_curve

- `{"bin": 1, "count": 166, "mean_probability": 1e-06, "observed_rate": 0.0}`
- `{"bin": 2, "count": 166, "mean_probability": 1e-06, "observed_rate": 0.0}`
- `{"bin": 3, "count": 165, "mean_probability": 1.2396204508207102e-06, "observed_rate": 0.0}`
- `{"bin": 4, "count": 165, "mean_probability": 3.0793797877250375e-05, "observed_rate": 0.0}`
- `{"bin": 5, "count": 165, "mean_probability": 0.0005031805173847744, "observed_rate": 0.0}`
- `{"bin": 6, "count": 165, "mean_probability": 0.00461776026897989, "observed_rate": 0.0}`
- `{"bin": 7, "count": 165, "mean_probability": 0.02663746347839558, "observed_rate": 0.012121212121212121}`
- `{"bin": 8, "count": 165, "mean_probability": 0.09717777425930138, "observed_rate": 0.08484848484848485}`
- `{"bin": 9, "count": 165, "mean_probability": 0.3104981115480713, "observed_rate": 0.3333333333333333}`
- `{"bin": 10, "count": 165, "mean_probability": 0.721058202058345, "observed_rate": 0.6424242424242425}`

###### 2

- states: 4411
- matches: 679
- brier: 0.1276527141218348
- log_loss: 0.38370875253276493
- match_macro_brier: 0.127792106465827
- match_macro_log_loss: 0.38454670898728127
- ece: 0.04534762904089108
- calibration_slope: 0.874186973571058
- calibration_intercept: -0.22040659168831828
- roc_auc: 0.9067555070200741

###### calibration_curve

- `{"bin": 1, "count": 442, "mean_probability": 0.004177640970386998, "observed_rate": 0.0}`
- `{"bin": 2, "count": 441, "mean_probability": 0.02551746437835984, "observed_rate": 0.006802721088435374}`
- `{"bin": 3, "count": 441, "mean_probability": 0.09474703059151096, "observed_rate": 0.1383219954648526}`
- `{"bin": 4, "count": 441, "mean_probability": 0.21432013857267374, "observed_rate": 0.25396825396825395}`
- `{"bin": 5, "count": 441, "mean_probability": 0.37615081821602714, "observed_rate": 0.35600907029478457}`
- `{"bin": 6, "count": 441, "mean_probability": 0.577379264126854, "observed_rate": 0.4557823129251701}`
- `{"bin": 7, "count": 441, "mean_probability": 0.7551242567604212, "observed_rate": 0.6598639455782312}`
- `{"bin": 8, "count": 441, "mean_probability": 0.8663780858586245, "observed_rate": 0.7777777777777778}`
- `{"bin": 9, "count": 441, "mean_probability": 0.9551315435411051, "observed_rate": 0.9410430839002267}`
- `{"bin": 10, "count": 441, "mean_probability": 0.9922335961651447, "observed_rate": 1.0}`

###### 3

- states: 4402
- matches: 677
- brier: 0.11828739604454144
- log_loss: 0.3598218664620237
- match_macro_brier: 0.11897248038871465
- match_macro_log_loss: 0.3620288435204061
- ece: 0.036478274718159155
- calibration_slope: 0.92482649999461
- calibration_intercept: -0.22501532394782583
- roc_auc: 0.9189181600359408

###### calibration_curve

- `{"bin": 1, "count": 441, "mean_probability": 0.004222852457759862, "observed_rate": 0.0}`
- `{"bin": 2, "count": 441, "mean_probability": 0.023110217729887146, "observed_rate": 0.0022675736961451248}`
- `{"bin": 3, "count": 440, "mean_probability": 0.08382827762814668, "observed_rate": 0.10681818181818181}`
- `{"bin": 4, "count": 440, "mean_probability": 0.19710953574519982, "observed_rate": 0.22045454545454546}`
- `{"bin": 5, "count": 440, "mean_probability": 0.3610220964067126, "observed_rate": 0.35}`
- `{"bin": 6, "count": 440, "mean_probability": 0.5789608588808495, "observed_rate": 0.4590909090909091}`
- `{"bin": 7, "count": 440, "mean_probability": 0.7545680186884786, "observed_rate": 0.6772727272727272}`
- `{"bin": 8, "count": 440, "mean_probability": 0.8743705875789142, "observed_rate": 0.8159090909090909}`
- `{"bin": 9, "count": 440, "mean_probability": 0.9556500036308017, "observed_rate": 0.9363636363636364}`
- `{"bin": 10, "count": 440, "mean_probability": 0.9924440214565367, "observed_rate": 1.0}`

###### 4

- states: 4404
- matches: 670
- brier: 0.11004076948611317
- log_loss: 0.33713908066410475
- match_macro_brier: 0.11207692849362033
- match_macro_log_loss: 0.34274919589504244
- ece: 0.038215706920368395
- calibration_slope: 0.9864401891485801
- calibration_intercept: -0.20769879347141676
- roc_auc: 0.9293886795968395

###### calibration_curve

- `{"bin": 1, "count": 441, "mean_probability": 0.0032107077406732516, "observed_rate": 0.0}`
- `{"bin": 2, "count": 441, "mean_probability": 0.02026902028078271, "observed_rate": 0.0}`
- `{"bin": 3, "count": 441, "mean_probability": 0.07467387420499838, "observed_rate": 0.09977324263038549}`
- `{"bin": 4, "count": 441, "mean_probability": 0.18223643447616278, "observed_rate": 0.1564625850340136}`
- `{"bin": 5, "count": 440, "mean_probability": 0.34166470768554186, "observed_rate": 0.37727272727272726}`
- `{"bin": 6, "count": 440, "mean_probability": 0.5704913576985853, "observed_rate": 0.43863636363636366}`
- `{"bin": 7, "count": 440, "mean_probability": 0.7592584067287416, "observed_rate": 0.6568181818181819}`
- `{"bin": 8, "count": 440, "mean_probability": 0.87460188599839, "observed_rate": 0.8568181818181818}`
- `{"bin": 9, "count": 440, "mean_probability": 0.9516853495166885, "observed_rate": 0.9636363636363636}`
- `{"bin": 10, "count": 440, "mean_probability": 0.99165540199563, "observed_rate": 1.0}`

###### 5

- states: 4372
- matches: 666
- brier: 0.10618659586191737
- log_loss: 0.3249693024765727
- match_macro_brier: 0.10514609728841719
- match_macro_log_loss: 0.3226216520714917
- ece: 0.044121579631345345
- calibration_slope: 1.0595663943270586
- calibration_intercept: -0.3060479972946072
- roc_auc: 0.93502898988134

###### calibration_curve

- `{"bin": 1, "count": 438, "mean_probability": 0.0027572018247622072, "observed_rate": 0.0}`
- `{"bin": 2, "count": 438, "mean_probability": 0.01992099034496002, "observed_rate": 0.0}`
- `{"bin": 3, "count": 437, "mean_probability": 0.07545069662816328, "observed_rate": 0.08466819221967964}`
- `{"bin": 4, "count": 437, "mean_probability": 0.18060834973287387, "observed_rate": 0.15331807780320367}`
- `{"bin": 5, "count": 437, "mean_probability": 0.3559040828065945, "observed_rate": 0.3524027459954233}`
- `{"bin": 6, "count": 437, "mean_probability": 0.5644000794890056, "observed_rate": 0.37757437070938216}`
- `{"bin": 7, "count": 437, "mean_probability": 0.7491918192140461, "observed_rate": 0.6155606407322655}`
- `{"bin": 8, "count": 437, "mean_probability": 0.8709950877773119, "observed_rate": 0.8924485125858124}`
- `{"bin": 9, "count": 437, "mean_probability": 0.950875517654071, "observed_rate": 0.9794050343249427}`
- `{"bin": 10, "count": 437, "mean_probability": 0.9917612946797622, "observed_rate": 1.0}`

###### 6

- states: 4246
- matches: 658
- brier: 0.09996001798139115
- log_loss: 0.308824115967964
- match_macro_brier: 0.10097314340529046
- match_macro_log_loss: 0.3118372557041579
- ece: 0.039126832982305605
- calibration_slope: 1.1060181672893692
- calibration_intercept: -0.32662333646992503
- roc_auc: 0.9423502927539987

###### calibration_curve

- `{"bin": 1, "count": 425, "mean_probability": 0.002425222259714696, "observed_rate": 0.0}`
- `{"bin": 2, "count": 425, "mean_probability": 0.017570208948200324, "observed_rate": 0.0}`
- `{"bin": 3, "count": 425, "mean_probability": 0.0681525548008486, "observed_rate": 0.05411764705882353}`
- `{"bin": 4, "count": 425, "mean_probability": 0.17056478103730147, "observed_rate": 0.14823529411764705}`
- `{"bin": 5, "count": 425, "mean_probability": 0.35350657122322915, "observed_rate": 0.3270588235294118}`
- `{"bin": 6, "count": 425, "mean_probability": 0.5701680938540987, "observed_rate": 0.36470588235294116}`
- `{"bin": 7, "count": 424, "mean_probability": 0.7511579856894165, "observed_rate": 0.7075471698113207}`
- `{"bin": 8, "count": 424, "mean_probability": 0.8795741954738169, "observed_rate": 0.8632075471698113}`
- `{"bin": 9, "count": 424, "mean_probability": 0.9539901001820175, "observed_rate": 0.9882075471698113}`
- `{"bin": 10, "count": 424, "mean_probability": 0.9913225663811509, "observed_rate": 1.0}`

###### 7

- states: 4190
- matches: 648
- brier: 0.09655203388307221
- log_loss: 0.29935150036926805
- match_macro_brier: 0.09628725499216406
- match_macro_log_loss: 0.29923577109978855
- ece: 0.042502354953277074
- calibration_slope: 1.149610036968084
- calibration_intercept: -0.3401580791105354
- roc_auc: 0.9453462268637197

###### calibration_curve

- `{"bin": 1, "count": 419, "mean_probability": 0.0017204550206789582, "observed_rate": 0.0}`
- `{"bin": 2, "count": 419, "mean_probability": 0.01426820764234908, "observed_rate": 0.0}`
- `{"bin": 3, "count": 419, "mean_probability": 0.06004763185767299, "observed_rate": 0.04295942720763723}`
- `{"bin": 4, "count": 419, "mean_probability": 0.14998624245018252, "observed_rate": 0.07875894988066826}`
- `{"bin": 5, "count": 419, "mean_probability": 0.3244295187515354, "observed_rate": 0.3269689737470167}`
- `{"bin": 6, "count": 419, "mean_probability": 0.5400856365098837, "observed_rate": 0.360381861575179}`
- `{"bin": 7, "count": 419, "mean_probability": 0.7278494908043744, "observed_rate": 0.6968973747016707}`
- `{"bin": 8, "count": 419, "mean_probability": 0.865334729665646, "observed_rate": 0.8138424821002387}`
- `{"bin": 9, "count": 419, "mean_probability": 0.9490537723363114, "observed_rate": 0.9952267303102625}`
- `{"bin": 10, "count": 419, "mean_probability": 0.9901411619220556, "observed_rate": 1.0}`

###### 8

- states: 4134
- matches: 639
- brier: 0.09660539420693799
- log_loss: 0.2996296479597562
- match_macro_brier: 0.09487293154253974
- match_macro_log_loss: 0.2953537811716181
- ece: 0.037216550488802534
- calibration_slope: 1.1281058886926663
- calibration_intercept: -0.3339928955021676
- roc_auc: 0.9450685713520729

###### calibration_curve

- `{"bin": 1, "count": 414, "mean_probability": 0.001399489583871082, "observed_rate": 0.0}`
- `{"bin": 2, "count": 414, "mean_probability": 0.011671950756093296, "observed_rate": 0.0}`
- `{"bin": 3, "count": 414, "mean_probability": 0.05021098055624957, "observed_rate": 0.03140096618357488}`
- `{"bin": 4, "count": 414, "mean_probability": 0.14480845178272947, "observed_rate": 0.0966183574879227}`
- `{"bin": 5, "count": 413, "mean_probability": 0.3167214756258501, "observed_rate": 0.3099273607748184}`
- `{"bin": 6, "count": 413, "mean_probability": 0.5353739533529012, "observed_rate": 0.3728813559322034}`
- `{"bin": 7, "count": 413, "mean_probability": 0.7219207896920795, "observed_rate": 0.6682808716707022}`
- `{"bin": 8, "count": 413, "mean_probability": 0.8623305242036414, "observed_rate": 0.8280871670702179}`
- `{"bin": 9, "count": 413, "mean_probability": 0.9495761038907063, "observed_rate": 0.9733656174334141}`
- `{"bin": 10, "count": 413, "mean_probability": 0.9886989720790998, "observed_rate": 1.0}`

###### 9

- states: 4057
- matches: 630
- brier: 0.09537569274918668
- log_loss: 0.2955433378887103
- match_macro_brier: 0.09362086539842772
- match_macro_log_loss: 0.2910260426449293
- ece: 0.03408961572604737
- calibration_slope: 1.1545254115967603
- calibration_intercept: -0.3145358578436987
- roc_auc: 0.9456308740249493

###### calibration_curve

- `{"bin": 1, "count": 406, "mean_probability": 0.0011614181627946968, "observed_rate": 0.0}`
- `{"bin": 2, "count": 406, "mean_probability": 0.010773702598328052, "observed_rate": 0.0}`
- `{"bin": 3, "count": 406, "mean_probability": 0.044997859914711114, "observed_rate": 0.012315270935960592}`
- `{"bin": 4, "count": 406, "mean_probability": 0.13506906078475328, "observed_rate": 0.06896551724137931}`
- `{"bin": 5, "count": 406, "mean_probability": 0.29895825256055686, "observed_rate": 0.27586206896551724}`
- `{"bin": 6, "count": 406, "mean_probability": 0.5004686875316879, "observed_rate": 0.4408866995073892}`
- `{"bin": 7, "count": 406, "mean_probability": 0.7002683169213088, "observed_rate": 0.5812807881773399}`
- `{"bin": 8, "count": 405, "mean_probability": 0.845644090382524, "observed_rate": 0.8518518518518519}`
- `{"bin": 9, "count": 405, "mean_probability": 0.9455116311415237, "observed_rate": 0.9555555555555556}`
- `{"bin": 10, "count": 405, "mean_probability": 0.9879246048461424, "observed_rate": 1.0}`

##### phase_absolute

###### death

- states: 9208
- matches: 465
- brier: 0.0727253889622002
- log_loss: 0.23024082439287444
- match_macro_brier: 0.06347877802198557
- match_macro_log_loss: 0.2061763441396507
- ece: 0.01889082424122498
- calibration_slope: 1.239015231885419
- calibration_intercept: -0.16640304682605753
- roc_auc: 0.9568092250813024

###### calibration_curve

- `{"bin": 1, "count": 921, "mean_probability": 1.4645158782806586e-06, "observed_rate": 0.0}`
- `{"bin": 2, "count": 921, "mean_probability": 0.00012846684592835594, "observed_rate": 0.0}`
- `{"bin": 3, "count": 921, "mean_probability": 0.0014691094910417248, "observed_rate": 0.0}`
- `{"bin": 4, "count": 921, "mean_probability": 0.00941704764918567, "observed_rate": 0.0}`
- `{"bin": 5, "count": 921, "mean_probability": 0.04207549982850674, "observed_rate": 0.0054288816503800215}`
- `{"bin": 6, "count": 921, "mean_probability": 0.12284274511873898, "observed_rate": 0.0749185667752443}`
- `{"bin": 7, "count": 921, "mean_probability": 0.266368196086214, "observed_rate": 0.19109663409337677}`
- `{"bin": 8, "count": 921, "mean_probability": 0.47636286405156586, "observed_rate": 0.46905537459283386}`
- `{"bin": 9, "count": 920, "mean_probability": 0.7306222006928319, "observed_rate": 0.7402173913043478}`
- `{"bin": 10, "count": 920, "mean_probability": 0.9282301013511706, "observed_rate": 0.9293478260869565}`

###### middle

- states: 38024
- matches: 658
- brier: 0.09106469744638751
- log_loss: 0.2846888650718029
- match_macro_brier: 0.082003235634494
- match_macro_log_loss: 0.2582188043369713
- ece: 0.03340135828557336
- calibration_slope: 1.2258488887326489
- calibration_intercept: -0.31673714530653263
- roc_auc: 0.9496002423980577

###### calibration_curve

- `{"bin": 1, "count": 3803, "mean_probability": 0.00073135586381409, "observed_rate": 0.0}`
- `{"bin": 2, "count": 3803, "mean_probability": 0.007722358476273818, "observed_rate": 0.0}`
- `{"bin": 3, "count": 3803, "mean_probability": 0.032508684220465565, "observed_rate": 0.004996055745464107}`
- `{"bin": 4, "count": 3803, "mean_probability": 0.10931313046654198, "observed_rate": 0.059426768340783594}`
- `{"bin": 5, "count": 3802, "mean_probability": 0.25524245558414876, "observed_rate": 0.1954234613361389}`
- `{"bin": 6, "count": 3802, "mean_probability": 0.4525495652837464, "observed_rate": 0.3750657548658601}`
- `{"bin": 7, "count": 3802, "mean_probability": 0.6449593782844758, "observed_rate": 0.5754865860073646}`
- `{"bin": 8, "count": 3802, "mean_probability": 0.8139142972051677, "observed_rate": 0.800894266175697}`
- `{"bin": 9, "count": 3802, "mean_probability": 0.9275669658806996, "observed_rate": 0.9400315623356128}`
- `{"bin": 10, "count": 3802, "mean_probability": 0.984086786615556, "observed_rate": 1.0}`

###### powerplay

- states: 26610
- matches: 681
- brier: 0.12650335060871398
- log_loss: 0.3840402241509145
- match_macro_brier: 0.12600694230156964
- match_macro_log_loss: 0.3827656179118567
- ece: 0.04042273197666212
- calibration_slope: 0.8560289669567481
- calibration_intercept: -0.18133392079188063
- roc_auc: 0.9073970723764202

###### calibration_curve

- `{"bin": 1, "count": 2661, "mean_probability": 0.0037566865129622646, "observed_rate": 0.0003757985719654265}`
- `{"bin": 2, "count": 2661, "mean_probability": 0.023886717695015307, "observed_rate": 0.020293122886133032}`
- `{"bin": 3, "count": 2661, "mean_probability": 0.08362959039749994, "observed_rate": 0.1386696730552424}`
- `{"bin": 4, "count": 2661, "mean_probability": 0.19637931767984082, "observed_rate": 0.22848553175497932}`
- `{"bin": 5, "count": 2661, "mean_probability": 0.3586731646278454, "observed_rate": 0.3543780533633972}`
- `{"bin": 6, "count": 2661, "mean_probability": 0.5646014510742546, "observed_rate": 0.4513340849304773}`
- `{"bin": 7, "count": 2661, "mean_probability": 0.7444573200650936, "observed_rate": 0.6392333709131905}`
- `{"bin": 8, "count": 2661, "mean_probability": 0.8690234708433382, "observed_rate": 0.7985719654265314}`
- `{"bin": 9, "count": 2661, "mean_probability": 0.9529021222022772, "observed_rate": 0.9402480270574972}`
- `{"bin": 10, "count": 2661, "mean_probability": 0.9920275011181999, "observed_rate": 0.9962420142803458}`

##### phase_relative

###### death

- states: 9208
- matches: 465
- brier: 0.0727253889622002
- log_loss: 0.23024082439287444
- match_macro_brier: 0.06347877802198557
- match_macro_log_loss: 0.2061763441396507
- ece: 0.01889082424122498
- calibration_slope: 1.239015231885419
- calibration_intercept: -0.16640304682605753
- roc_auc: 0.9568092250813024

###### calibration_curve

- `{"bin": 1, "count": 921, "mean_probability": 1.4645158782806586e-06, "observed_rate": 0.0}`
- `{"bin": 2, "count": 921, "mean_probability": 0.00012846684592835594, "observed_rate": 0.0}`
- `{"bin": 3, "count": 921, "mean_probability": 0.0014691094910417248, "observed_rate": 0.0}`
- `{"bin": 4, "count": 921, "mean_probability": 0.00941704764918567, "observed_rate": 0.0}`
- `{"bin": 5, "count": 921, "mean_probability": 0.04207549982850674, "observed_rate": 0.0054288816503800215}`
- `{"bin": 6, "count": 921, "mean_probability": 0.12284274511873898, "observed_rate": 0.0749185667752443}`
- `{"bin": 7, "count": 921, "mean_probability": 0.266368196086214, "observed_rate": 0.19109663409337677}`
- `{"bin": 8, "count": 921, "mean_probability": 0.47636286405156586, "observed_rate": 0.46905537459283386}`
- `{"bin": 9, "count": 920, "mean_probability": 0.7306222006928319, "observed_rate": 0.7402173913043478}`
- `{"bin": 10, "count": 920, "mean_probability": 0.9282301013511706, "observed_rate": 0.9293478260869565}`

###### middle

- states: 38024
- matches: 658
- brier: 0.09106469744638751
- log_loss: 0.2846888650718029
- match_macro_brier: 0.082003235634494
- match_macro_log_loss: 0.2582188043369713
- ece: 0.03340135828557336
- calibration_slope: 1.2258488887326489
- calibration_intercept: -0.31673714530653263
- roc_auc: 0.9496002423980577

###### calibration_curve

- `{"bin": 1, "count": 3803, "mean_probability": 0.00073135586381409, "observed_rate": 0.0}`
- `{"bin": 2, "count": 3803, "mean_probability": 0.007722358476273818, "observed_rate": 0.0}`
- `{"bin": 3, "count": 3803, "mean_probability": 0.032508684220465565, "observed_rate": 0.004996055745464107}`
- `{"bin": 4, "count": 3803, "mean_probability": 0.10931313046654198, "observed_rate": 0.059426768340783594}`
- `{"bin": 5, "count": 3802, "mean_probability": 0.25524245558414876, "observed_rate": 0.1954234613361389}`
- `{"bin": 6, "count": 3802, "mean_probability": 0.4525495652837464, "observed_rate": 0.3750657548658601}`
- `{"bin": 7, "count": 3802, "mean_probability": 0.6449593782844758, "observed_rate": 0.5754865860073646}`
- `{"bin": 8, "count": 3802, "mean_probability": 0.8139142972051677, "observed_rate": 0.800894266175697}`
- `{"bin": 9, "count": 3802, "mean_probability": 0.9275669658806996, "observed_rate": 0.9400315623356128}`
- `{"bin": 10, "count": 3802, "mean_probability": 0.984086786615556, "observed_rate": 1.0}`

###### powerplay

- states: 26610
- matches: 681
- brier: 0.12650335060871398
- log_loss: 0.3840402241509145
- match_macro_brier: 0.12600694230156964
- match_macro_log_loss: 0.3827656179118567
- ece: 0.04042273197666212
- calibration_slope: 0.8560289669567481
- calibration_intercept: -0.18133392079188063
- roc_auc: 0.9073970723764202

###### calibration_curve

- `{"bin": 1, "count": 2661, "mean_probability": 0.0037566865129622646, "observed_rate": 0.0003757985719654265}`
- `{"bin": 2, "count": 2661, "mean_probability": 0.023886717695015307, "observed_rate": 0.020293122886133032}`
- `{"bin": 3, "count": 2661, "mean_probability": 0.08362959039749994, "observed_rate": 0.1386696730552424}`
- `{"bin": 4, "count": 2661, "mean_probability": 0.19637931767984082, "observed_rate": 0.22848553175497932}`
- `{"bin": 5, "count": 2661, "mean_probability": 0.3586731646278454, "observed_rate": 0.3543780533633972}`
- `{"bin": 6, "count": 2661, "mean_probability": 0.5646014510742546, "observed_rate": 0.4513340849304773}`
- `{"bin": 7, "count": 2661, "mean_probability": 0.7444573200650936, "observed_rate": 0.6392333709131905}`
- `{"bin": 8, "count": 2661, "mean_probability": 0.8690234708433382, "observed_rate": 0.7985719654265314}`
- `{"bin": 9, "count": 2661, "mean_probability": 0.9529021222022772, "observed_rate": 0.9402480270574972}`
- `{"bin": 10, "count": 2661, "mean_probability": 0.9920275011181999, "observed_rate": 0.9962420142803458}`

##### japan_role

###### japan_chasing

- states: 497
- matches: 4
- brier: 0.01022595746320196
- log_loss: 0.07552110180538826
- match_macro_brier: 0.010374179179522793
- match_macro_log_loss: 0.07608757407184993
- ece: 0.06606705877945604
- calibration_slope: None
- calibration_intercept: None
- roc_auc: None

###### calibration_curve

- `{"bin": 1, "count": 50, "mean_probability": 0.00212783365919099, "observed_rate": 0.0}`
- `{"bin": 2, "count": 50, "mean_probability": 0.008051398424172178, "observed_rate": 0.0}`
- `{"bin": 3, "count": 50, "mean_probability": 0.013984686479389701, "observed_rate": 0.0}`
- `{"bin": 4, "count": 50, "mean_probability": 0.02320562760991826, "observed_rate": 0.0}`
- `{"bin": 5, "count": 50, "mean_probability": 0.03919894007195974, "observed_rate": 0.0}`
- `{"bin": 6, "count": 50, "mean_probability": 0.057354192834103056, "observed_rate": 0.0}`
- `{"bin": 7, "count": 50, "mean_probability": 0.07541368845011046, "observed_rate": 0.0}`
- `{"bin": 8, "count": 49, "mean_probability": 0.09696681243215198, "observed_rate": 0.0}`
- `{"bin": 9, "count": 49, "mean_probability": 0.1287045214683269, "observed_rate": 0.0}`
- `{"bin": 10, "count": 49, "mean_probability": 0.22062478522089735, "observed_rate": 0.0}`

###### japan_defending

- states: 1123
- matches: 10
- brier: 0.11730725334133196
- log_loss: 0.34596008083432717
- match_macro_brier: 0.12213961416595512
- match_macro_log_loss: 0.35734513205437374
- ece: 0.14018775331970457
- calibration_slope: 0.7110196292039194
- calibration_intercept: -1.6361073387004554
- roc_auc: 0.8643902710524851

###### calibration_curve

- `{"bin": 1, "count": 113, "mean_probability": 8.53300071830111e-05, "observed_rate": 0.0}`
- `{"bin": 2, "count": 113, "mean_probability": 0.0030995003156878637, "observed_rate": 0.0}`
- `{"bin": 3, "count": 113, "mean_probability": 0.008248589583146185, "observed_rate": 0.0}`
- `{"bin": 4, "count": 112, "mean_probability": 0.024236995709916602, "observed_rate": 0.0}`
- `{"bin": 5, "count": 112, "mean_probability": 0.07233613838550161, "observed_rate": 0.0}`
- `{"bin": 6, "count": 112, "mean_probability": 0.14086075144548355, "observed_rate": 0.05357142857142857}`
- `{"bin": 7, "count": 112, "mean_probability": 0.24209657805433757, "observed_rate": 0.10714285714285714}`
- `{"bin": 8, "count": 112, "mean_probability": 0.40803911859771314, "observed_rate": 0.21428571428571427}`
- `{"bin": 9, "count": 112, "mean_probability": 0.6099024932264953, "observed_rate": 0.22321428571428573}`
- `{"bin": 10, "count": 112, "mean_probability": 0.8430535543006263, "observed_rate": 0.3482142857142857}`

###### other

- states: 72222
- matches: 667
- brier: 0.10193203249150855
- log_loss: 0.3148393858212377
- match_macro_brier: 0.09087205343919239
- match_macro_log_loss: 0.2834983323658838
- ece: 0.02463063768280859
- calibration_slope: 1.0452553656655577
- calibration_intercept: -0.22375644350490054
- roc_auc: 0.9361331942846758

###### calibration_curve

- `{"bin": 1, "count": 7223, "mean_probability": 0.0005838917095928509, "observed_rate": 0.0}`
- `{"bin": 2, "count": 7223, "mean_probability": 0.008158041572028742, "observed_rate": 0.0004153398864737644}`
- `{"bin": 3, "count": 7222, "mean_probability": 0.03648090349925142, "observed_rate": 0.02076986984214899}`
- `{"bin": 4, "count": 7222, "mean_probability": 0.11835683674584607, "observed_rate": 0.10938798116865134}`
- `{"bin": 5, "count": 7222, "mean_probability": 0.2632981058032697, "observed_rate": 0.2453613957352534}`
- `{"bin": 6, "count": 7222, "mean_probability": 0.456377389470873, "observed_rate": 0.3865965106618665}`
- `{"bin": 7, "count": 7222, "mean_probability": 0.6568871173736356, "observed_rate": 0.5859872611464968}`
- `{"bin": 8, "count": 7222, "mean_probability": 0.8211510017037776, "observed_rate": 0.7783162558847965}`
- `{"bin": 9, "count": 7222, "mean_probability": 0.9305355218895842, "observed_rate": 0.9329825533093326}`
- `{"bin": 10, "count": 7222, "mean_probability": 0.9864396861223766, "observed_rate": 0.9958460260315702}`

##### match_format

###### full

- states: 73842
- matches: 681
- brier: 0.10154862540238965
- log_loss: 0.31370192141539577
- match_macro_brier: 0.09085837371853005
- match_macro_log_loss: 0.2833644483184664
- ece: 0.02654830066070857
- calibration_slope: 1.0461166804247797
- calibration_intercept: -0.24539372763082376
- roc_auc: 0.9363876073529155

###### calibration_curve

- `{"bin": 1, "count": 7385, "mean_probability": 0.0005716512984838079, "observed_rate": 0.0}`
- `{"bin": 2, "count": 7385, "mean_probability": 0.00793727265029207, "observed_rate": 0.00040622884224779957}`
- `{"bin": 3, "count": 7384, "mean_probability": 0.03487583251987209, "observed_rate": 0.01868905742145179}`
- `{"bin": 4, "count": 7384, "mean_probability": 0.11204821709262969, "observed_rate": 0.10197724810400867}`
- `{"bin": 5, "count": 7384, "mean_probability": 0.251471166663629, "observed_rate": 0.22467497291440952}`
- `{"bin": 6, "count": 7384, "mean_probability": 0.4433917813023964, "observed_rate": 0.38068797399783316}`
- `{"bin": 7, "count": 7384, "mean_probability": 0.645679442014533, "observed_rate": 0.5689328277356447}`
- `{"bin": 8, "count": 7384, "mean_probability": 0.8147161718037846, "observed_rate": 0.7608342361863488}`
- `{"bin": 9, "count": 7384, "mean_probability": 0.9278179103896294, "observed_rate": 0.9295774647887324}`
- `{"bin": 10, "count": 7384, "mean_probability": 0.98601946617158, "observed_rate": 0.9952600216684724}`

#### terminal_inclusive

- states: 74524
- matches: 681
- brier: 0.10061931185878292
- log_loss: 0.31083111431426114
- match_macro_brier: 0.090104478482266
- match_macro_log_loss: 0.2809805217873059
- ece: 0.026328527305327833
- calibration_slope: 1.0461435724136712
- calibration_intercept: -0.24544711943129965
- roc_auc: 0.9375774704542744

##### calibration_curve

- `{"bin": 1, "count": 7453, "mean_probability": 0.000481457277686606, "observed_rate": 0.0}`
- `{"bin": 2, "count": 7453, "mean_probability": 0.007468777134665304, "observed_rate": 0.0001341741580571582}`
- `{"bin": 3, "count": 7453, "mean_probability": 0.033687923173110854, "observed_rate": 0.017710988863544882}`
- `{"bin": 4, "count": 7453, "mean_probability": 0.11024246436700157, "observed_rate": 0.10049644438481148}`
- `{"bin": 5, "count": 7452, "mean_probability": 0.250153286830186, "observed_rate": 0.22289318303811056}`
- `{"bin": 6, "count": 7452, "mean_probability": 0.4436321543392689, "observed_rate": 0.38097155126140636}`
- `{"bin": 7, "count": 7452, "mean_probability": 0.6476774541096322, "observed_rate": 0.5709876543209876}`
- `{"bin": 8, "count": 7452, "mean_probability": 0.817427648502636, "observed_rate": 0.7652979066022544}`
- `{"bin": 9, "count": 7452, "mean_probability": 0.9302160719396142, "observed_rate": 0.9323671497584541}`
- `{"bin": 10, "count": 7452, "mean_probability": 0.9872438634832074, "observed_rate": 0.9961084272678475}`
