db::setPrefValue leStopLevel -value 0 -scope [db::getNext [de::getContexts -window 9]];
after 10
db::setPrefValue leStartLevel -value 0 -scope [db::getNext [de::getContexts -window 9]];
after 10
de::redraw -window 9
after 10

# Row 2: Selecting devices at Y=1485
db::setPrefValue deSelectMode -value Replace -scope [db::getScopes [db::getNext [de::getContexts -window 9]]];
after 10
ide::selectByRegion -region rectangle -point {12.157 1.435}
after 10
de::endDrag {18.521 2.085} -context [db::getNext [de::getContexts -window 9]]
after 10

# Moving to Y=1253
ile::stretch -point {12.207 1.485}
after 10
de::endDrag {12.207 1.253} -context [db::getNext [de::getContexts -window 9]]
after 10

# Row 3: Selecting devices at Y=2285
db::setPrefValue deSelectMode -value Replace -scope [db::getScopes [db::getNext [de::getContexts -window 9]]];
after 10
ide::selectByRegion -region rectangle -point {12.157 2.235}
after 10
de::endDrag {18.521 2.885} -context [db::getNext [de::getContexts -window 9]]
after 10

# Moving to Y=1821
ile::stretch -point {12.207 2.285}
after 10
de::endDrag {12.207 1.821} -context [db::getNext [de::getContexts -window 9]]
after 10

# Row 4: Selecting devices at Y=3085
db::setPrefValue deSelectMode -value Replace -scope [db::getScopes [db::getNext [de::getContexts -window 9]]];
after 10
ide::selectByRegion -region rectangle -point {12.157 3.035}
after 10
de::endDrag {18.521 3.685} -context [db::getNext [de::getContexts -window 9]]
after 10

# Moving to Y=2389
ile::stretch -point {12.207 3.085}
after 10
de::endDrag {12.207 2.389} -context [db::getNext [de::getContexts -window 9]]
after 10

# Row 5: Selecting devices at Y=3885
db::setPrefValue deSelectMode -value Replace -scope [db::getScopes [db::getNext [de::getContexts -window 9]]];
after 10
ide::selectByRegion -region rectangle -point {12.157 3.835}
after 10
de::endDrag {18.521 4.485} -context [db::getNext [de::getContexts -window 9]]
after 10

# Moving to Y=2957
ile::stretch -point {12.207 3.885}
after 10
de::endDrag {12.207 2.957} -context [db::getNext [de::getContexts -window 9]]
after 10

# Row 6: Selecting devices at Y=4685
db::setPrefValue deSelectMode -value Replace -scope [db::getScopes [db::getNext [de::getContexts -window 9]]];
after 10
ide::selectByRegion -region rectangle -point {12.157 4.635}
after 10
de::endDrag {18.521 5.285} -context [db::getNext [de::getContexts -window 9]]
after 10

# Moving to Y=3525
ile::stretch -point {12.207 4.685}
after 10
de::endDrag {12.207 3.525} -context [db::getNext [de::getContexts -window 9]]
after 10

# Row 7: Selecting devices at Y=5485
db::setPrefValue deSelectMode -value Replace -scope [db::getScopes [db::getNext [de::getContexts -window 9]]];
after 10
ide::selectByRegion -region rectangle -point {12.157 5.435}
after 10
de::endDrag {18.521 6.085} -context [db::getNext [de::getContexts -window 9]]
after 10

# Moving to Y=4093
ile::stretch -point {12.207 5.485}
after 10
de::endDrag {12.207 4.093} -context [db::getNext [de::getContexts -window 9]]
after 10

# Row 8: Selecting devices at Y=6285
db::setPrefValue deSelectMode -value Replace -scope [db::getScopes [db::getNext [de::getContexts -window 9]]];
after 10
ide::selectByRegion -region rectangle -point {12.157 6.235}
after 10
de::endDrag {18.521 6.885} -context [db::getNext [de::getContexts -window 9]]
after 10

# Moving to Y=4661
ile::stretch -point {12.207 6.285}
after 10
de::endDrag {12.207 4.661} -context [db::getNext [de::getContexts -window 9]]
after 10

# Row 9: Selecting devices at Y=7085
db::setPrefValue deSelectMode -value Replace -scope [db::getScopes [db::getNext [de::getContexts -window 9]]];
after 10
ide::selectByRegion -region rectangle -point {12.157 7.035}
after 10
de::endDrag {18.521 7.685} -context [db::getNext [de::getContexts -window 9]]
after 10

# Moving to Y=5229
ile::stretch -point {12.207 7.085}
after 10
de::endDrag {12.207 5.229} -context [db::getNext [de::getContexts -window 9]]
after 10

# Row 10: Selecting devices at Y=7885
db::setPrefValue deSelectMode -value Replace -scope [db::getScopes [db::getNext [de::getContexts -window 9]]];
after 10
ide::selectByRegion -region rectangle -point {12.157 7.835}
after 10
de::endDrag {18.521 8.485} -context [db::getNext [de::getContexts -window 9]]
after 10

# Moving to Y=5797
ile::stretch -point {12.207 7.885}
after 10
de::endDrag {12.207 5.797} -context [db::getNext [de::getContexts -window 9]]
after 10

# Row 11: Selecting devices at Y=8685
db::setPrefValue deSelectMode -value Replace -scope [db::getScopes [db::getNext [de::getContexts -window 9]]];
after 10
ide::selectByRegion -region rectangle -point {12.157 8.635}
after 10
de::endDrag {18.521 9.285} -context [db::getNext [de::getContexts -window 9]]
after 10

# Moving to Y=6365
ile::stretch -point {12.207 8.685}
after 10
de::endDrag {12.207 6.365} -context [db::getNext [de::getContexts -window 9]]
after 10

# Row 12: Selecting devices at Y=9485
db::setPrefValue deSelectMode -value Replace -scope [db::getScopes [db::getNext [de::getContexts -window 9]]];
after 10
ide::selectByRegion -region rectangle -point {12.157 9.435}
after 10
de::endDrag {18.521 10.085} -context [db::getNext [de::getContexts -window 9]]
after 10

# Moving to Y=6933
ile::stretch -point {12.207 9.485}
after 10
de::endDrag {12.207 6.933} -context [db::getNext [de::getContexts -window 9]]
after 10
