# Auto-generated TCL code for POCUT rectangles
# Processing 7 unique rows
# Window Number: 2

# Setup layer visibility
db::setAttr selectable -of [de::getLPPs -from [de::getContexts -window 2]] -value false
gi::setField {allSelectable} -value {false} -in [db::getAttr toolbar -of [gi::getAssistants leObjectLayerPanel -from [gi::getWindows 2]]]
db::setAttr visible -of [de::getLPPs -from [de::getContexts -window 2]] -value false
gi::setField {allVisible} -value {false} -in [db::getAttr toolbar -of [gi::getAssistants leObjectLayerPanel -from [gi::getWindows 2]]]

de::setActiveLPP [de::getLPPs {POCUT drawing} -from [oa::DesignFind hello_again automationtesting layout]]

# ROW 1: Y = 5881 microns
le::createRectangle {{3.723 5.861} {6.829 5.901}} -design [ed] -lpp {POCUT drawing}

# ROW 2: Y = 6449 microns
le::createRectangle {{3.723 6.429} {6.829 6.469}} -design [ed] -lpp {POCUT drawing}

# ROW 3: Y = 7017 microns
le::createRectangle {{3.723 6.997} {6.829 7.037}} -design [ed] -lpp {POCUT drawing}

# ROW 4: Y = 7585 microns
le::createRectangle {{3.723 7.565} {6.829 7.605}} -design [ed] -lpp {POCUT drawing}

# ROW 5: Y = 8153 microns
le::createRectangle {{3.723 8.133} {6.829 8.173}} -design [ed] -lpp {POCUT drawing}

# ROW 6: Y = 8721 microns
le::createRectangle {{3.723 8.701} {6.829 8.741}} -design [ed] -lpp {POCUT drawing}

# ROW 7: Y = 9289 microns
le::createRectangle {{3.723 9.269} {6.829 9.309}} -design [ed] -lpp {POCUT drawing}
