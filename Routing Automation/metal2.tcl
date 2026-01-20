# Auto-generated TCL code for horizontal wire creation
# Processing 7 unique rows
# Metal Width: 1.7
# Window Number: 2
# Wire X range: 3.723000 to 6.835000 (from x=3723 to x=6535+300 microns)

# Setup layer visibility
db::setAttr selectable -of [de::getLPPs -from [de::getContexts -window 2]] -value false
gi::setField {allSelectable} -value {false} -in [db::getAttr toolbar -of [gi::getAssistants leObjectLayerPanel -from [gi::getWindows 2]]]
db::setAttr visible -of [de::getLPPs -from [de::getContexts -window 2]] -value false
gi::setField {allVisible} -value {false} -in [db::getAttr toolbar -of [gi::getAssistants leObjectLayerPanel -from [gi::getWindows 2]]]

# Set active layer
de::setActiveLPP [de::getLPPs {M2 drawing} -from [oa::DesignFind hello_again automationtesting layout]]

# ======================================================================
# ROW 1: Y = 5881 microns (20 components)
# ======================================================================
# Row orientation: N
# Using N/FN offsets: [146, 50, 308, 402, 496]

# Wire at offset 146 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 6.027000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 6.027000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 50 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 5.931000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 5.931000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 308 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 6.189000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 6.189000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 402 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 6.283000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 6.283000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 496 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 6.377000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 6.377000] \
    -context [db::getNext [de::getContexts -window 2]]

# ======================================================================
# ROW 2: Y = 6449 microns (20 components)
# ======================================================================
# Row orientation: FS
# Using S/FS offsets: [158, 253, 508, 412, 63]

# Wire at offset 158 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 6.607000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 6.607000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 253 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 6.702000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 6.702000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 508 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 6.957000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 6.957000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 412 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 6.861000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 6.861000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 63 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 6.512000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 6.512000] \
    -context [db::getNext [de::getContexts -window 2]]

# ======================================================================
# ROW 3: Y = 7017 microns (20 components)
# ======================================================================
# Row orientation: FS
# Using S/FS offsets: [158, 253, 508, 412, 63]

# Wire at offset 158 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 7.175000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 7.175000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 253 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 7.270000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 7.270000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 508 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 7.525000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 7.525000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 412 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 7.429000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 7.429000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 63 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 7.080000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 7.080000] \
    -context [db::getNext [de::getContexts -window 2]]

# ======================================================================
# ROW 4: Y = 7585 microns (20 components)
# ======================================================================
# Row orientation: N
# Using N/FN offsets: [146, 50, 308, 402, 496]

# Wire at offset 146 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 7.731000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 7.731000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 50 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 7.635000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 7.635000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 308 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 7.893000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 7.893000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 402 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 7.987000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 7.987000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 496 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 8.081000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 8.081000] \
    -context [db::getNext [de::getContexts -window 2]]

# ======================================================================
# ROW 5: Y = 8153 microns (20 components)
# ======================================================================
# Row orientation: N
# Using N/FN offsets: [146, 50, 308, 402, 496]

# Wire at offset 146 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 8.299000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 8.299000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 50 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 8.203000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 8.203000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 308 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 8.461000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 8.461000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 402 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 8.555000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 8.555000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 496 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 8.649000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 8.649000] \
    -context [db::getNext [de::getContexts -window 2]]

# ======================================================================
# ROW 6: Y = 8721 microns (20 components)
# ======================================================================
# Row orientation: FS
# Using S/FS offsets: [158, 253, 508, 412, 63]

# Wire at offset 158 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 8.879000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 8.879000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 253 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 8.974000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 8.974000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 508 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 9.229000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 9.229000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 412 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 9.133000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 9.133000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 63 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 8.784000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 8.784000] \
    -context [db::getNext [de::getContexts -window 2]]

# ======================================================================
# ROW 7: Y = 9289 microns (20 components)
# ======================================================================
# Row orientation: N
# Using N/FN offsets: [146, 50, 308, 402, 496]

# Wire at offset 146 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 9.435000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 9.435000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 50 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 9.339000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 9.339000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 308 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 9.597000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 9.597000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 402 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 9.691000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 9.691000] \
    -context [db::getNext [de::getContexts -window 2]]

# Wire at offset 496 microns from row base
ile::createInterconnect
de::addPoint \
    [list 3.723000 9.785000] \
    -context [db::getNext [de::getContexts -window 2]]
de::completeShape \
    [list 6.835000 9.785000] \
    -context [db::getNext [de::getContexts -window 2]]

# ======================================================================
# Total wires created: 35
# ======================================================================

# Restore layer visibility
db::setAttr selectable -of [de::getLPPs -from [de::getContexts -window 2]] -value true
gi::setField {allSelectable} -value {true} -in [db::getAttr toolbar -of [gi::getAssistants leObjectLayerPanel -from [gi::getWindows 2]]]
db::setAttr visible -of [de::getLPPs -from [de::getContexts -window 2]] -value true
gi::setField {allVisible} -value {true} -in [db::getAttr toolbar -of [gi::getAssistants leObjectLayerPanel -from [gi::getWindows 2]]]
# Set active layer
de::setActiveLPP [de::getLPPs {M2 drawing} -from [oa::DesignFind hello_again automationtesting layout]]